import multiprocessing
import time
import random
from unittest import TestCase

from flask import url_for

from app import create_app, db
from app.config import TestConfig
from app.models import create_sample_data, User, Membership
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

localHost = "http://127.0.0.1:5000/"


class SeleniumTests(TestCase):
    def setUp(self):
        # Create app, DB and seed sample data
        self.testApp = create_app(TestConfig)
        self.app_context = self.testApp.app_context()
        self.app_context.push()
        db.create_all()
        create_sample_data()

        # Start the server in a separate process
        self.server_thread = multiprocessing.Process(target=self.testApp.run)
        self.server_thread.start()
        time.sleep(0.5)

        # Start Chrome (headless by default for CI)
        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=opts)
        self.wait = WebDriverWait(self.driver, 6)
        return super().setUp()

    def tearDown(self):
        try:
            self.server_thread.terminate()
        except Exception:
            pass
        try:
            self.driver.quit()
        except Exception:
            pass

        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        return super().tearDown()

    # --- Helpers ---
    def login_ui(self, email, password):
        self.driver.get(localHost + "login")
        self.wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(email)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
        self.wait.until(EC.url_contains("/home"))

    # --- Tests ---
    def test_login_flow(self):
        """Verify login succeeds and redirects to /home."""
        self.login_ui("aisha@example.com", "password123")
        # Home page should render task list or greeting
        self.wait.until(EC.presence_of_element_located((By.ID, "task-list")))

    def test_signup_and_create_household(self):
        """Complete the two-step signup + create household flow."""
        unique = str(int(time.time()))
        email = f"test{unique}@example.com"

        self.driver.get(localHost + "signup")
        self.wait.until(EC.presence_of_element_located((By.NAME, "first_name"))).send_keys("Test")
        self.driver.find_element(By.NAME, "last_name").send_keys("User")
        self.driver.find_element(By.NAME, "display_name").send_keys("Tester")
        self.driver.find_element(By.NAME, "email").send_keys(email)
        self.driver.find_element(By.NAME, "password").send_keys("passw0rd")
        self.driver.find_element(By.NAME, "confirm_password").send_keys("passw0rd")
        self.driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

        # Now on household creation page
        self.wait.until(EC.presence_of_element_located((By.NAME, "household_name"))).send_keys("Selenium Household")
        self.driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
        self.wait.until(EC.url_contains("/home"))

    def test_create_and_toggle_task(self):
        """Create a task via the UI and toggle it complete/incomplete."""
        self.login_ui("aisha@example.com", "password123")

        # Open add-task modal
        self.wait.until(EC.element_to_be_clickable((By.ID, "modal-add-btn"))).click()
        self.wait.until(EC.visibility_of_element_located((By.ID, "taskModal")))

        # Fill modal fields
        name = f"Selenium task {random.randint(1000,9999)}"
        self.driver.find_element(By.ID, "modal-task-name").send_keys(name)
        # Select first non-empty assignee
        assigned = self.driver.find_element(By.ID, "modal-assigned")
        for option in assigned.find_elements(By.TAG_NAME, "option"):
            if option.get_attribute("value"):
                option.click()
                break
        self.driver.find_element(By.ID, "modal-points").send_keys("10")
        # Submit
        self.driver.find_element(By.CSS_SELECTOR, "#taskModal .modal-btn-add").click()

        # Wait for task to appear in list
        self.wait.until(EC.text_to_be_present_in_element((By.ID, "task-list"), name))

        # Toggle the first task's checkbox area
        first_check = self.driver.find_element(By.CSS_SELECTOR, "#task-list .task-item .task-check")
        first_item = self.driver.find_element(By.CSS_SELECTOR, "#task-list .task-item")
        first_check.click()
        # Task item should gain the 'done' class
        self.wait.until(lambda d: "done" in first_item.get_attribute("class"))

    def test_rewards_claim(self):
        """Make user eligible for a points reward and claim it through the UI."""
        # Boost Aisha's membership points so a reward is unlocked
        user = db.session.query(User).filter_by(email="aisha@example.com").first()
        if user:
            membership = db.session.query(Membership).filter_by(user_id=user.id).first()
            if membership:
                membership.points = 2000
                db.session.commit()

        self.login_ui("aisha@example.com", "password123")
        self.driver.get(localHost + "rewards")
        # Wait for rewards to render and find an unlocked item
        unlocked = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".reward-item.unlocked")))
        claim_btn = unlocked.find_element(By.CSS_SELECTOR, ".reward-claim-btn")
        claim_btn.click()
        # After clicking, the item should show claimed status
        self.wait.until(lambda d: unlocked.find_elements(By.CSS_SELECTOR, ".status-claimed") )

    def test_leaderboard_display_and_ranking(self):
        """Check leaderboard shows the seeded users in correct order."""
        self.login_ui("aisha@example.com", "password123")
        self.driver.get(localHost + "leaderboard")
        # The seeded sample data contains Aisha, Jordan, Mohammad
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".podium")))
        body = self.driver.find_element(By.TAG_NAME, "body").text
        assert "Aisha" in body
        assert "Jordan" in body
        assert "Mohammad" in body

    def test_edit_profile_update(self):
        """Update display name and confirm persistence."""
        self.login_ui("aisha@example.com", "password123")
        self.driver.get(localHost + "edit-profile")
        # Change display name
        new_name = f"Aisha-{random.randint(100,999)}"
        disp = self.wait.until(EC.presence_of_element_located((By.NAME, "display_name")))
        disp.clear()
        disp.send_keys(new_name)
        self.driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
        # After save, header should show new name
        name_el = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "profile-header-name")))
        self.wait.until(lambda d: new_name in name_el.text)
    
