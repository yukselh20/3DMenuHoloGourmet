import requests
import sys
import json
import time
import io
import zipfile
from datetime import datetime

class RestaurantMenuAPITester:
    def __init__(self, base_url="https://dinemodel3d.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_items = []

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
            
        if headers:
            test_headers.update(headers)
            
        if files:
            # Remove Content-Type for file uploads
            test_headers.pop('Content-Type', None)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers=test_headers)
                else:
                    response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_register(self, email, password):
        """Test user registration"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={"email": email, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            return True
        return False

    def test_login(self, email, password):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={"email": email, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            return True
        return False

    def test_get_user_profile(self):
        """Test getting current user profile"""
        success, response = self.run_test(
            "Get User Profile",
            "GET",
            "auth/me",
            200
        )
        if success and 'id' in response:
            self.user_id = response['id']
            return True
        return False

    def test_create_menu_item(self):
        """Test creating a menu item"""
        menu_data = {
            "name": "Test Grilled Salmon",
            "description": "Fresh Atlantic salmon grilled to perfection with herbs",
            "price": 24.99,
            "allergens": ["fish"],
            "dimensions_cm": {
                "diameter": 28,
                "height": 10
            }
        }
        
        success, response = self.run_test(
            "Create Menu Item",
            "POST",
            "menu-items",
            200,
            data=menu_data
        )
        
        if success and 'id' in response:
            self.created_items.append(response['id'])
            return response['id']
        return None

    def test_get_menu_items(self):
        """Test getting user's menu items"""
        success, response = self.run_test(
            "Get Menu Items",
            "GET",
            "menu-items",
            200
        )
        return success

    def test_get_single_menu_item(self, item_id):
        """Test getting a single menu item"""
        success, response = self.run_test(
            "Get Single Menu Item",
            "GET",
            f"menu-items/{item_id}",
            200
        )
        return success

    def test_update_menu_item(self, item_id):
        """Test updating a menu item"""
        update_data = {
            "price": 26.99,
            "description": "Updated: Fresh Atlantic salmon grilled to perfection with herbs and lemon"
        }
        
        success, response = self.run_test(
            "Update Menu Item",
            "PUT",
            f"menu-items/{item_id}",
            200,
            data=update_data
        )
        return success

    def create_test_zip_file(self):
        """Create a test zip file with dummy images"""
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Create 5 dummy image files
            for i in range(5):
                # Create a minimal dummy image content (just some bytes)
                dummy_content = b"dummy_image_content_" + str(i).encode() * 100
                zip_file.writestr(f"image_{i+1}.jpg", dummy_content)
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    def test_upload_images(self, item_id):
        """Test uploading images for photogrammetry"""
        zip_content = self.create_test_zip_file()
        
        files = {
            'file': ('test_images.zip', zip_content, 'application/zip')
        }
        
        success, response = self.run_test(
            "Upload Images",
            "POST",
            f"menu-items/{item_id}/upload-images",
            200,
            files=files
        )
        
        if success and 'job_id' in response:
            return response['job_id']
        return None

    def test_job_status(self, item_id):
        """Test getting job status"""
        success, response = self.run_test(
            "Get Job Status",
            "GET",
            f"jobs/{item_id}",
            200
        )
        return success, response

    def test_public_menu_item(self, item_id):
        """Test public menu item endpoint"""
        success, response = self.run_test(
            "Get Public Menu Item",
            "GET",
            f"public/menu-item/{item_id}",
            200
        )
        return success

    def test_delete_menu_item(self, item_id):
        """Test deleting a menu item"""
        success, response = self.run_test(
            "Delete Menu Item",
            "DELETE",
            f"menu-items/{item_id}",
            200
        )
        return success

    def wait_for_job_completion(self, item_id, max_wait_time=30):
        """Wait for photogrammetry job to complete"""
        print(f"\n⏳ Waiting for job completion (max {max_wait_time}s)...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            success, response = self.test_job_status(item_id)
            if success and 'status' in response:
                status = response['status']
                print(f"   Job status: {status}")
                
                if status == 'COMPLETED':
                    print("✅ Job completed successfully!")
                    return True
                elif status == 'FAILED':
                    print(f"❌ Job failed: {response.get('error_message', 'Unknown error')}")
                    return False
                    
            time.sleep(3)
        
        print("⏰ Job did not complete within timeout")
        return False

def main():
    # Setup
    tester = RestaurantMenuAPITester()
    test_email = f"test_{datetime.now().strftime('%H%M%S')}@restaurant.com"
    test_password = "testpass123"

    print("🚀 Starting 3D Restaurant Menu API Tests")
    print(f"Backend URL: {tester.base_url}")
    print(f"Test Email: {test_email}")

    # Test 1: Root endpoint
    if not tester.test_root_endpoint():
        print("❌ Root endpoint failed, stopping tests")
        return 1

    # Test 2: User Registration
    if not tester.test_register(test_email, test_password):
        print("❌ Registration failed, stopping tests")
        return 1

    # Test 3: Get user profile
    if not tester.test_get_user_profile():
        print("❌ Get user profile failed, stopping tests")
        return 1

    # Test 4: Create menu item
    item_id = tester.test_create_menu_item()
    if not item_id:
        print("❌ Menu item creation failed, stopping tests")
        return 1

    # Test 5: Get menu items
    if not tester.test_get_menu_items():
        print("❌ Get menu items failed")

    # Test 6: Get single menu item
    if not tester.test_get_single_menu_item(item_id):
        print("❌ Get single menu item failed")

    # Test 7: Update menu item
    if not tester.test_update_menu_item(item_id):
        print("❌ Update menu item failed")

    # Test 8: Upload images
    job_id = tester.test_upload_images(item_id)
    if not job_id:
        print("❌ Image upload failed")
    else:
        # Test 9: Wait for job completion
        job_completed = tester.wait_for_job_completion(item_id)
        if job_completed:
            print("✅ Photogrammetry processing completed!")
        else:
            print("⚠️ Job did not complete in time, but upload was successful")

    # Test 10: Public menu item access
    if not tester.test_public_menu_item(item_id):
        print("❌ Public menu item access failed")

    # Test 11: Test login with existing user
    tester.token = None  # Clear token
    if not tester.test_login(test_email, test_password):
        print("❌ Login with existing user failed")

    # Cleanup: Delete created items
    for item_id in tester.created_items:
        tester.test_delete_menu_item(item_id)

    # Print results
    print(f"\n📊 Test Results:")
    print(f"   Tests run: {tester.tests_run}")
    print(f"   Tests passed: {tester.tests_passed}")
    print(f"   Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())