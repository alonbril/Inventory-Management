from cryptography.fernet import Fernet
import base64
import datetime
import json
import os


class LicenseValidator:
    def __init__(self):
        # Use the exact same key as in key_generator.py
        self.secret_key = b'jJzteGTIlciymjoiAm-0oyJUrgAIT5gDesSq351l-1I='  # Make sure this matches your key_generator.py
        self.license_file = 'license.json'

    def validate_key(self, serial_key, company_name):
        try:
            # Check if license file exists and is valid
            if self._check_stored_license():
                return True

            print(f"Validating key for company: {company_name}")  # Debug print

            # Generate expected data
            current_date = datetime.datetime.now().strftime("%Y%m")
            expected_data = f"{company_name}:{current_date}".encode()

            try:
                # Create Fernet instance
                fernet = Fernet(self.secret_key)

                # Reconstruct full key (add padding)
                while len(serial_key) % 4:
                    serial_key += '='

                print(f"Attempting to decrypt key: {serial_key}")  # Debug print

                # Decrypt the key
                decrypted_data = fernet.decrypt(base64.urlsafe_b64decode(serial_key))
                print(f"Decrypted data: {decrypted_data}")  # Debug print
                print(f"Expected data: {expected_data}")  # Debug print

                if decrypted_data == expected_data:
                    print("Key validated successfully!")  # Debug print
                    self._store_license(serial_key, company_name)
                    return True
                else:
                    print("Key validation failed - data mismatch")  # Debug print
                    return False

            except Exception as e:
                print(f"Decryption error: {str(e)}")  # Debug print
                return False

        except Exception as e:
            print(f"Validation error: {str(e)}")  # Debug print
            return False

    def _store_license(self, serial_key, company_name):
        license_data = {
            'serial_key': serial_key,
            'company_name': company_name,
            'activation_date': datetime.datetime.now().strftime("%Y-%m-%d")
        }
        with open(self.license_file, 'w') as f:
            json.dump(license_data, f)

    def _check_stored_license(self):
        try:
            if not os.path.exists(self.license_file):
                return False

            with open(self.license_file, 'r') as f:
                license_data = json.load(f)

            return self.validate_key(
                license_data['serial_key'],
                license_data['company_name']
            )
        except:
            return False