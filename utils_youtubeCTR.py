from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from seleniumwire import webdriver

from fake_useragent import UserAgent
from loguru import logger
import random
from datetime import datetime
import yt_dlp
import time
import configparser
import cx_Oracle
import os
from dotenv import load_dotenv

load_dotenv()

ORA_USERNAME = os.getenv('ORA_USERNAME')
ORA_PASSWORD = os.getenv('ORA_PASSWORD')
ORA_DSN = os.getenv('ORA_DSN')

INTIAL_ORA_PROC_CALL = os.getenv('INTIAL_ORA_PROC_CALL')
CONFIRM_ORA_PROC_CALL = os.getenv('CONFIRM_ORA_PROC_CALL')

# intialize the logger
logger.add("logger.log", rotation="5 MB", level="INFO")
def get_logger():
    return logger

# util functions to read and load probabilities
def load_probabilities(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    signed_prob = int(config['Probabilities']['signed'])
    unsigned_prob = int(config['Probabilities']['unsigned'])
    total_prob = signed_prob + unsigned_prob
    return signed_prob / total_prob, unsigned_prob / total_prob

# util function to make choice with weighted probabilities
def make_choice(probabilities):
    choice = random.choices([True, False], probabilities)
    return choice[0]

# get proxy details from oracle
def getProxy():
    logger.info("Requesting Data frm Oracle")
    with cx_Oracle.connect(user=ORA_USERNAME, password=ORA_PASSWORD, dsn=ORA_DSN) as conn:
        with conn.cursor() as c:
            HOST = c.var(cx_Oracle.STRING)
            USERNAME = c.var(cx_Oracle.STRING)
            PASS = c.var(cx_Oracle.STRING)
            KEYWORD = c.var(cx_Oracle.STRING)
            TARGET_CHANNEL = c.var(cx_Oracle.STRING)
            COUNTRY = c.var(cx_Oracle.STRING)
            UNI_KEY = c.var(cx_Oracle.STRING)
            
            c.callproc(INTIAL_ORA_PROC_CALL, [HOST,USERNAME,PASS,KEYWORD,TARGET_CHANNEL,COUNTRY,UNI_KEY])
            
            HOST = HOST.getvalue()
            USERNAME = USERNAME.getvalue()
            PASS = PASS.getvalue()
            KEYWORD = KEYWORD.getvalue()
            TARGET_CHANNEL = TARGET_CHANNEL.getvalue()
            COUNTRY = COUNTRY.getvalue()
            UNI_KEY = UNI_KEY.getvalue()
    logger.info("Data received from Oracle")
    CREDS  = {"PROXY_RACK_DNS": HOST, "USERNAME": USERNAME, "PASSWORD": PASS, "KEYWORD": KEYWORD, "TARGET_CHANNEL": TARGET_CHANNEL, "UNI_KEY": UNI_KEY}
    return CREDS

# # send confirmation back to oracle
def send_confimation_to_oracle(driver,KEY,PARAMS):
    if driver!=None:
        IP_ADDRESS = driver.execute_script("return fetch('https://api64.ipify.org?format=json').then(response => response.json()).then(data => data.ip);")
        logger.info(f"Current IP Address: {IP_ADDRESS}")
    else:
        IP_ADDRESS = "NULL"
    
    if PARAMS['success'].lower()=="yes":
        CURRENT_LINK = driver.current_url
        logger.info(f"Current Link: {CURRENT_LINK}")
    else:
        CURRENT_LINK = "Null"
    try:
        with cx_Oracle.connect(user=ORA_USERNAME, password=ORA_PASSWORD, dsn=ORA_DSN) as conn:
            with conn.cursor() as c:
                logger.info("Sending confirmation to Oracle")
                logger.success(f"{CONFIRM_ORA_PROC_CALL} {[KEY,PARAMS['notes'],IP_ADDRESS,PARAMS['success'],PARAMS['counter'],CURRENT_LINK]}")
                c.callproc(CONFIRM_ORA_PROC_CALL, [KEY,PARAMS['notes'],IP_ADDRESS,PARAMS['success'],PARAMS['counter'],CURRENT_LINK])
                logger.info("Confirmation sent to Oracle")
    except Exception as e:
        logger.error(f"Unable to send confirmation to Oracle, Error: {e}")
    return

# util function to intialize the driver
def getDriver(PROXY_RACK_DNS, username, password, with_profile=True):
    chrome_options = Options()

    PROFILE_ASSIGNED_COUNTRIES = {
        1: "US",
        2: "GB",
        4: "CA",
        6: "AU",
        3: "IN",
        5: "RU",
        7: "PH"
    }
    
    user_agent = UserAgent().random
    if with_profile:
        profile_choice = random.choice([1,2,3,4,5,6])
        logger.info(f"Profile Choice: {profile_choice}")
        logger.info(f"Country: {PROFILE_ASSIGNED_COUNTRIES[profile_choice]}")
        chrome_options.add_argument(f"--user-data-dir=/home/administrator/.config/google-chrome")
        chrome_options.add_argument(f"--profile-directory=Profile {profile_choice}")
        username = username+f";country={PROFILE_ASSIGNED_COUNTRIES[profile_choice]}"
        print(username)
    
    proxy = f"{username}:{password}@{PROXY_RACK_DNS}"
    
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-browser-side-navigation")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"user-agent={user_agent}")

    excluded_switches = [
        "enable-automation",
        "enable-logging",
        "disable-popup-blocking",
        "disable-gpu",
    ]
    chrome_options.add_experimental_option("excludeSwitches", excluded_switches)
    
    driver = webdriver.Chrome(options=chrome_options, seleniumwire_options={"proxy": {"http": f"http://{proxy}", "https": f"https://{proxy}"}}); driver.maximize_window()
    logger.info("Intializing the driver")
    #driver = webdriver.Chrome(options=chrome_options); driver.maximize_window()
    logger.info("Driver intialized")
    
    user_agent = driver.execute_script("return navigator.userAgent;")
    logger.info(f"User Agent: {user_agent}")
    
    return driver
        
def navigate_to_youtube(driver,KEY):
    try:
        driver.get("https://www.youtube.com/")
        logger.info("Opened Youtube.com")
    except:
        import os
        screenshot_dir= "./image_logs"
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        screenshot_path = os.path.join(screenshot_dir, f"screenshot_{timestamp}.png")
        driver.save_screenshot(screenshot_path); time.sleep(5)
        
        error_message = "ERROR: Unable to open Youtube.com, POOR INTERNET/CONNECTION ISSUE...EXITING the code...."
        logger.error(error_message)
        PARAMS = {
            "success": "No",
            "notes": error_message,
            "counter": 0
        }
        send_confimation_to_oracle(driver,KEY,PARAMS)
        driver.quit(); exit(0)

    try:
        dialog = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, 'dialog'))
        )
        logger.info("Cookie Banner Found")
        button = dialog.find_element(By.CSS_SELECTOR, 'button[aria-label="Accept the use of cookies and other data for the purposes described"]')
        ActionChains(driver).move_to_element(button).click().perform()
        logger.info("Accept All Clicked")
        time.sleep(5)
    except:
        logger.info("NO cookie banner found...continuing with the code")
        
    return driver

def getWatch_time(videoLink):
    with yt_dlp.YoutubeDL({}) as ydl:
        video_info = ydl.extract_info(videoLink, download=False)
        video_length = video_info.get('duration')
        
    logger.info(f"Total duration: {video_length}")
    watch_percentage = random.uniform(0.5, 0.65)
    logger.info(f"Choosen Watch percentage: {watch_percentage}")
    watch_duration = int(video_length * watch_percentage)
    logger.info(f"Choosen Watch Duration in seconds: {watch_duration}")
    return watch_duration

def skip_or_watch_ad(driver,max_attempts=2, ad_timeout=300, skip_ad_probability=0.5):
   
    for attempt in range(max_attempts):
        try:
            ad_overlay = WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "ytp-ad-player-overlay-skip-or-preview"))
            )
            logger.info("Waiting for the ad")

            should_skip = random.random() < skip_ad_probability

            if should_skip:
                logger.info("Decided to Skip the ad")
                ad_skip_button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "ytp-ad-skip-button"))
                )
                action = ActionChains(driver)
                action.move_to_element(ad_skip_button).click().perform()
                logger.info("Skipped the ad")
            else:
                logger.info("Decided not to Skip the ad")
                try:
                    WebDriverWait(driver, ad_timeout).until(
                        EC.invisibility_of_element_located((By.CLASS_NAME, "ytp-ad-player-overlay-skip-or-preview"))
                    )
                except:
                    pass
            logger.info("Completed Watching AD")
            break  

        except Exception as e:
            logger.error(f"Error during ad watching attempt {attempt + 1}; Ad not found to skip")
            time.sleep(1)
      
    return driver

def search_for_Video(driver,KEY,KEYWORD,TARGET_CHANNEL):
    curr_time = f"===> Current Time: {datetime.now().strftime('%H:%M:%S')}\n"
    logger.info(curr_time)
    
    overlay = WebDriverWait(driver, 120).until(
        EC.invisibility_of_element_located((By.ID, 'dialog'))
    )
    search_box = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.NAME, "search_query")))
    action = ActionChains(driver)
    action.move_to_element(search_box).click().perform()
    
    msg_1 = f"Searching for video...\nKeyword:{KEYWORD}"
    logger.info(msg_1)
    
    action = ActionChains(driver)
    action.move_to_element(search_box).click().perform()
    for letter in KEYWORD:
        search_box.send_keys(letter)
        time.sleep(random.randint(0,1000)/1000)
    time.sleep(3)
    search_box.send_keys(Keys.ENTER)
    
    msg_2 = f"Keyword entered: {KEYWORD}"
    logger.info(msg_2)
    
    WebDriverWait(driver, 100).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "a#video-title")
    ))
    last_index = 0 
    target_not_found = True
    prev_content_count = 0 
    prev_scroll_height = 0
    PREVIOUS_VIDEO_LINK = None
    TARGET_VIDEO_INDEX_COUNTER = 0 

    while target_not_found:
        if last_index > 400:
            break

        master_cmp = driver.find_elements(By.CSS_SELECTOR, 'div.text-wrapper.style-scope.ytd-video-renderer')
        channel_names = [master.find_elements(By.CSS_SELECTOR, "yt-formatted-string.style-scope.ytd-channel-name a")[1] for master in master_cmp]
        video_links = [master.find_elements(By.CSS_SELECTOR, "a#video-title")[0] for master in master_cmp]

        channel_names = channel_names[last_index:]
        video_links = video_links[last_index:]

        current_content_count = len(channel_names) 
        current_scroll_height = driver.execute_script("return document.documentElement.scrollHeight")
        if (current_content_count == prev_content_count) and (current_scroll_height == prev_scroll_height):
            logger.info("No new videos loaded. Stopping scrolling.")
            target_not_found = True
            break
        else:
            prev_content_count = current_content_count  
            prev_scroll_height = current_scroll_height 

        for channelName, videoLink in zip(channel_names, video_links):
            msg_3 = f"Target: {TARGET_CHANNEL}; Found: {channelName.text}; Video Index: {TARGET_VIDEO_INDEX_COUNTER}"
            logger.info(msg_3)
            
            if TARGET_CHANNEL.lower() in channelName.text.lower():
                print("==== Video FOUND =====")
                logger.debug("==== Video FOUND =====")
                target_not_found = False
                TARGET_CHANNEL_ELEMENT = channelName
                TARGET_VIDEO_LINK = videoLink
                break
            else:
                driver.execute_script("arguments[0].scrollIntoView({block: 'start', inline: 'nearest', behavior: 'smooth'});", channelName)
                time.sleep(0.5)
            last_index += 1; TARGET_VIDEO_INDEX_COUNTER+=1
            
            PREVIOUS_VIDEO_LINK = videoLink
            
        time.sleep(random.randint(7, 15))
        
    if target_not_found:
        msg_4 = f"Target Channel: {TARGET_CHANNEL} not found in the first 400 videos. Exiting the code..."
        logger.error(msg_4)
        PARAMS = {
            "success": "No",
            "notes": msg_4,
            "counter": 0
        }
        send_confimation_to_oracle(driver,KEY,PARAMS)
        driver.quit(); exit(0)
    
    targetElements = {"TARGET_CHANNEL_ELEMENT": TARGET_CHANNEL_ELEMENT, "TARGET_VIDEO_LINK": TARGET_VIDEO_LINK, "PREVIOUS_VIDEO_LINK": PREVIOUS_VIDEO_LINK}
    return driver,targetElements,TARGET_VIDEO_INDEX_COUNTER


def random_like_video(driver):
    logger.info("Randomly Deciding to like the video")
    driver.execute_script("window.scrollBy(0, 500);");time.sleep(5)
    likeFlag = random.choice([True, False])
    if likeFlag:
        logger.info("chose to like the video")
        # select the like button parent element
        button_element = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, 'segmented-like-button'))
        )
        # select the like button
        like_button = button_element.find_element(By.TAG_NAME,"button")
        # get the like button into the view
        driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", like_button)   
        time.sleep(1)
        try:
            # hit like button if not already liked
            if like_button.get_attribute('aria-pressed') == 'false':
                ActionChains(driver).move_to_element(like_button).click().perform()
                logger.info("Video Liked")
                likeFlag = True
            else:
                logger.info("Video already liked")
                likeFlag = True
        except Exception as e:
            logger.error(f"Error while liking the video: {e}")
            likeFlag = False
        
        return driver,likeFlag
    
    logger.info("chose not to like the video"); likeFlag = False
    return driver, likeFlag

def random_comment_video(driver):
    logger.info("Randomly Deciding to comment on the video")
    driver.execute_script("window.scrollBy(0, 500);");time.sleep(5)
    makeCommentFlag = random.choice([True, False])
    if makeCommentFlag:
        logger.info("chose to comment on the video")
        # select the comment box
        comment_box = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, 'placeholder-area'))
        )
        # get the comment box into the view
        driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", comment_box)   
        time.sleep(1)

        random_forex_comments = [
                "Thanks for sharing this insightful video!",
                "I've learned a lot from watching this. Great content!",
                "Your video is a valuable resource for forex enthusiasts.",
                "I appreciate the effort you put into creating this video.",
                "This video is a gem for anyone interested in forex trading.",
                "Kudos to you for making such informative content!",
                "I'm grateful for the knowledge you've shared in this video.",
                "Your video has been a real eye-opener for me. Thank you!",
                "I can't thank you enough for this helpful video.",
                "This video is like a mentor to me. Much appreciated!",
                "Your insights in this video are truly invaluable.",
                "I've hit the like button before the video even started  that's how much I appreciate your content!",
                "I've bookmarked this video for future reference. Amazing work!",
                "You make complex forex concepts easy to understand. Thanks!",
                "Your video has motivated me to dive deeper into forex trading.",
                "I've watched this video multiple times  it's that good!",
                "Your content is a goldmine for forex enthusiasts like me.",
                "You're doing an amazing job of educating us. Keep it up!",
                "I've subscribed to your channel after watching this video.",
                "This video is a must-watch for anyone in the forex game.",
                "Your passion for forex really shines through in this video.",
                "I appreciate your dedication to educating the forex community.",
                "Your video is like a breath of fresh air in the forex world.",
                "Your video has added tremendous value to my forex journey.",
                "I'm grateful for the time and effort you put into this video.",
                "I've learned more in this video than in weeks of research. Thank you!"
        ]
        choosen_comment = random.choice(random_forex_comments)
        logger.info(f"Randomly choosen comment is: {choosen_comment}")
        try:
            # click and type the comment
            actions = ActionChains(driver)
            actions.move_to_element(comment_box).perform()
            actions.click(comment_box).perform()
            for letter in choosen_comment:
                actions.send_keys(letter)
                time.sleep(random.randint(0, 1000) / 1000)
            actions.perform()
            logger.info("Comment typed")
            # post the comment by cliking "submit" button
            comment_submit_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'submit-button'))
            )
            actions.move_to_element(comment_submit_button).perform()
            actions.click(comment_submit_button).perform()
            driver.execute_script("window.scrollTo(0, 0);")
            logger.info("Comment posted")
            commentFlag = True
        except Exception as e:
            commentFlag = True
            logger.error(f"Error while commenting: {e}")
        
        return driver, commentFlag
    
    driver.execute_script("window.scrollTo(0, 0);")
    logger.info("chose not to comment on the video"); commentFlag = False
    return driver, commentFlag