#!/usr/bin/env python3
"""
Integration test for MCP Memory → Google Drive

Tests:
1. Local MCP memory directory exists
2. OAuth credentials work
3. Upload to Google Drive
4. Download from Google Drive
5. File integrity (checksums match)

Usage:
    pip install PyDrive2
    python test_integration.py
"""

import os
import sys
import hashlib
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# Test configuration
MCP_MEMORY_PATH = os.path.expanduser("~/.mcp-memory/")
TEST_FILE = "test_vector_store.pkl"
TEST_CONTENT = b"This is a test MCP memory file with binary data: \x00\x01\x02\x03"

# Color codes
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def log_success(msg):
    print(f"{GREEN}✅ {msg}{NC}")

def log_error(msg):
    print(f"{RED}❌ {msg}{NC}")

def log_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{NC}")

def log_info(msg):
    print(f"{BLUE}ℹ️  {msg}{NC}")

def calculate_hash(file_path):
    """Calculate SHA256 hash of file"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        sha256.update(f.read())
    return sha256.hexdigest()

def test_1_local_directory():
    """Test 1: Check if MCP memory directory exists"""
    print("\n" + "=" * 60)
    print("Test 1: Local MCP Memory Directory")
    print("=" * 60)

    if os.path.exists(MCP_MEMORY_PATH):
        log_success(f"Directory exists: {MCP_MEMORY_PATH}")

        # Check if writable
        test_file = os.path.join(MCP_MEMORY_PATH, ".test_write")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            log_success("Directory is writable")
            return True
        except Exception as e:
            log_error(f"Directory not writable: {e}")
            return False
    else:
        log_warning("Directory does not exist, creating...")
        try:
            os.makedirs(MCP_MEMORY_PATH)
            log_success(f"Created directory: {MCP_MEMORY_PATH}")
            return True
        except Exception as e:
            log_error(f"Could not create directory: {e}")
            return False

def test_2_authentication():
    """Test 2: Authenticate with Google Drive"""
    print("\n" + "=" * 60)
    print("Test 2: Google Drive Authentication")
    print("=" * 60)

    try:
        gauth = GoogleAuth()
        gauth.LoadCredentialsFile("mycreds.txt")

        if gauth.credentials is None:
            log_info("First time authentication - browser will open")
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            log_info("Refreshing expired credentials")
            gauth.Refresh()
        else:
            gauth.Authorize()

        gauth.SaveCredentialsFile("mycreds.txt")

        drive = GoogleDrive(gauth)

        log_success("Authentication successful")
        return drive
    except Exception as e:
        log_error(f"Authentication failed: {e}")
        return None

def test_3_create_test_file():
    """Test 3: Create test file"""
    print("\n" + "=" * 60)
    print("Test 3: Create Test File")
    print("=" * 60)

    test_file_path = os.path.join(MCP_MEMORY_PATH, TEST_FILE)

    try:
        with open(test_file_path, 'wb') as f:
            f.write(TEST_CONTENT)

        file_hash = calculate_hash(test_file_path)
        log_success(f"Created test file: {test_file_path}")
        log_info(f"SHA256: {file_hash}")
        log_info(f"Size: {len(TEST_CONTENT)} bytes")

        return test_file_path, file_hash
    except Exception as e:
        log_error(f"Could not create test file: {e}")
        return None, None

def test_4_upload(drive, test_file_path):
    """Test 4: Upload to Google Drive"""
    print("\n" + "=" * 60)
    print("Test 4: Upload to Google Drive")
    print("=" * 60)

    try:
        # Check if file already exists
        query = f"title='{TEST_FILE}' and trashed=false"
        file_list = drive.ListFile({'q': query}).GetList()

        if file_list:
            log_info(f"File already exists (ID: {file_list[0]['id']}), updating...")
            file_drive = file_list[0]
        else:
            log_info("Creating new file on Drive")
            file_drive = drive.CreateFile({
                'title': TEST_FILE,
                'parents': [{'id': 'root'}]
            })

        # Upload
        file_drive.SetContentFile(test_file_path)
        file_drive.Upload()

        log_success(f"Upload successful")
        log_info(f"File ID: {file_drive['id']}")
        log_info(f"File name: {file_drive['title']}")

        return file_drive['id']
    except Exception as e:
        log_error(f"Upload failed: {e}")
        return None

def test_5_download(drive, file_id, original_hash):
    """Test 5: Download from Google Drive and verify"""
    print("\n" + "=" * 60)
    print("Test 5: Download and Verify Integrity")
    print("=" * 60)

    download_path = os.path.join(MCP_MEMORY_PATH, f"{TEST_FILE}.downloaded")

    try:
        # Download
        file_drive = drive.CreateFile({'id': file_id})
        file_drive.GetContentFile(download_path)

        log_success(f"Download successful: {download_path}")

        # Verify hash
        download_hash = calculate_hash(download_path)
        log_info(f"Original SHA256:  {original_hash}")
        log_info(f"Download SHA256:  {download_hash}")

        if original_hash == download_hash:
            log_success("File integrity verified - hashes match!")

            # Clean up
            os.remove(download_path)
            log_info("Cleaned up test download")

            return True
        else:
            log_error("File integrity failed - hashes do not match!")
            return False

    except Exception as e:
        log_error(f"Download failed: {e}")
        return False

def test_6_list_files(drive):
    """Test 6: List files on Google Drive"""
    print("\n" + "=" * 60)
    print("Test 6: List Files on Google Drive")
    print("=" * 60)

    try:
        query = "trashed=false"
        file_list = drive.ListFile({'q': query, 'maxResults': 10}).GetList()

        log_success(f"Found {len(file_list)} file(s)")

        for i, file_drive in enumerate(file_list, 1):
            print(f"   {i}. {file_drive['title']}")
            print(f"      ID: {file_drive['id']}")
            print(f"      Modified: {file_drive.get('modifiedDate', 'N/A')}")

        return True
    except Exception as e:
        log_error(f"List files failed: {e}")
        return False

def cleanup(drive):
    """Cleanup: Remove test file from Drive"""
    print("\n" + "=" * 60)
    print("Cleanup")
    print("=" * 60)

    try:
        # Remove local test file
        test_file_path = os.path.join(MCP_MEMORY_PATH, TEST_FILE)
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
            log_success(f"Removed local test file")

        # Remove from Drive
        query = f"title='{TEST_FILE}' and trashed=false"
        file_list = drive.ListFile({'q': query}).GetList()

        if file_list:
            for file_drive in file_list:
                file_drive.Delete()
                log_success(f"Removed file from Drive (ID: {file_drive['id']})")
        else:
            log_info("No test files found on Drive")

    except Exception as e:
        log_warning(f"Cleanup warning: {e}")

def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("MCP Memory → Google Drive Integration Test")
    print("=" * 70)

    results = []

    # Test 1: Local directory
    result_1 = test_1_local_directory()
    results.append(("Local directory", result_1))

    if not result_1:
        print("\n" + RED + "❌ Cannot proceed without local directory" + NC)
        return

    # Test 2: Authentication
    drive = test_2_authentication()
    results.append(("Authentication", drive is not None))

    if not drive:
        print("\n" + RED + "❌ Cannot proceed without authentication" + NC)
        return

    # Test 3: Create test file
    test_file_path, file_hash = test_3_create_test_file()
    results.append(("Create test file", test_file_path is not None))

    if not test_file_path:
        print("\n" + RED + "❌ Cannot proceed without test file" + NC)
        return

    # Test 4: Upload
    file_id = test_4_upload(drive, test_file_path)
    results.append(("Upload to Drive", file_id is not None))

    if not file_id:
        print("\n" + RED + "❌ Cannot proceed without upload" + NC)
        return

    # Test 5: Download and verify
    result_5 = test_5_download(drive, file_id, file_hash)
    results.append(("Download and verify", result_5))

    # Test 6: List files
    result_6 = test_6_list_files(drive)
    results.append(("List files", result_6))

    # Cleanup
    cleanup(drive)

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = GREEN + "PASS" + NC if result else RED + "FAIL" + NC
        print(f"  {status}  {test_name}")

    print()
    print("=" * 70)

    if passed == total:
        print(GREEN + f"✅ All tests passed! ({passed}/{total})" + NC)
        print()
        print("🎉 Your MCP Memory → Google Drive integration is working!")
        print()
        print("Next steps:")
        print("  1. Run: rclone sync ~/.mcp-memory/ gdrive:mcp-memory/")
        print("  2. Or: python mcp_auto_sync.py")
        print("  3. Check: https://drive.google.com")
        return 0
    else:
        print(RED + f"❌ Some tests failed ({passed}/{total} passed)" + NC)
        return 1

if __name__ == "__main__":
    sys.exit(main())
