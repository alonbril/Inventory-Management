from cryptography.fernet import Fernet
import base64
import datetime
import json
import os


class LicenseValidator:
    def __init__(self):
        self.secret_key = b'jJzteGTIlciymjoiAm-0oyJUrgAIT5gDesSq351l-1I='
        self.license_file = 'license.json'

    def validate_key(self, serial_key, company_name):
        try:
            # Check if license file exists and is valid
            if self._check_stored_license():
                return True

            try:
                # Create Fernet instance
                fernet = Fernet(self.secret_key)

                # Decode the key
                encrypted_data = base64.urlsafe_b64decode(serial_key)
                decrypted_data = fernet.decrypt(encrypted_data)

                # Parse the JSON data
                license_data = json.loads(decrypted_data.decode())

                # Verify company name
                if license_data['company'] != company_name:
                    print("Company name mismatch")
                    return False

                # Check expiration
                current_timestamp = int(datetime.datetime.now().timestamp())
                if license_data['expires'] != -1 and current_timestamp > license_data['expires']:
                    print("License expired")
                    return False

                # If we get here, the license is valid
                self._store_license(serial_key, company_name)
                return True

            except Exception as e:
                print(f"Decryption error: {str(e)}")
                return False

        except Exception as e:
            print(f"Validation error: {str(e)}")
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