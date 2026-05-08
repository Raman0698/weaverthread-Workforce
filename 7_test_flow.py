from playwright.sync_api import sync_playwright

def run(playwright):
    # Launch browser so you can see it working
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    
    # 1. Navigate to the local frontend server
    page.goto("http://localhost:3000")
    
    # 2. Click the specific toggle button to show the registration form
    page.click("#btnShowRegister")
    
    # 3. Use the UNIQUE IDs defined in your HTML to avoid ambiguity
    page.fill("#registerUsername", "LegendaryRaman")
    page.fill("#registerPassword", "SecurePass123!")
    
    # 4. Click the specific Registration Submit button
    page.click("#btnRegisterSubmit")
    
    # Give it a second to process before closing
    page.wait_for_timeout(2000)
    print("Registration flow completed successfully!")
    browser.close()

with sync_playwright() as playwright:
    run(playwright)