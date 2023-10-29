from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from loguru import logger
from collections import OrderedDict
import random
import time
import re

from utils_youtubeCTR import *

# intialize the logger
logger = get_logger()

# ================================= STRATEGY 1 ============================================== #
"""
    FUNCTION TO CLICK ON EITHER TARGET VIDEO OR PREVIOUS VIDEO
"""
def perform_startegy_1(driver, KEY, TARGET_VIDEO_LINK, PREVIOUS_VIDEO_LINK):
    # make a choice to click on either target video or previous video
    target_or_previous = random.choice(["previous", "target","previous"])
    logger.info(f"Chosen video: {target_or_previous}")
    if target_or_previous == "target":
        # get the watch duration
        watch_duration = getWatch_time(TARGET_VIDEO_LINK.get_attribute("href"))
        logger.info(f"Watch duration: {watch_duration}")
        # get the video into the view
        driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", TARGET_VIDEO_LINK)
        # open video in new tab
        action = ActionChains(driver)
        action.move_to_element(TARGET_VIDEO_LINK).perform()
        action.key_down(Keys.CONTROL).click(TARGET_VIDEO_LINK).key_up(Keys.CONTROL).perform()
        driver.switch_to.window(driver.window_handles[1])
        logger.info("Target video opened in new tab")
        
        time.sleep(10)        
        driver = skip_or_watch_ad(driver)
        return driver, watch_duration
    
    else:
        # get the watch duration
        watch_duration = getWatch_time(TARGET_VIDEO_LINK.get_attribute("href"))
        logger.info(f"Watch duration: {watch_duration}")
        # get the video into the view
        driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", PREVIOUS_VIDEO_LINK)
        # open video in new tab
        action = ActionChains(driver)
        action.move_to_element(PREVIOUS_VIDEO_LINK).perform()
        action.key_down(Keys.CONTROL).click(PREVIOUS_VIDEO_LINK).key_up(Keys.CONTROL).perform()
        driver.switch_to.window(driver.window_handles[1])
        logger.info("Previous video opened in new tab")
        
        # choose a random watch time for the previous video
        random_watchtime = random.randint(30,50)
        logger.info(f"The previous video will be watched for {random_watchtime} seconds")
        driver = skip_or_watch_ad(driver)
        time.sleep(random_watchtime)
        
        msg5 = f"Watched the previous video for {random_watchtime} seconds"
        logger.info(msg5)
        
        logger.info("Closing the previous video tab")
        driver.close(); driver.switch_to.window(driver.window_handles[0])
        msg6 = "Closed the previous video tab and Swiched to the main tab"
        logger.info(msg6)
        
        logger.info("Opening the target video in new tab")
        # get the video into the view
        driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", TARGET_VIDEO_LINK)
        # open video in new tab
        action = ActionChains(driver)
        action.move_to_element(TARGET_VIDEO_LINK).perform()
        action.key_down(Keys.CONTROL).click(TARGET_VIDEO_LINK).key_up(Keys.CONTROL).perform()
        driver.switch_to.window(driver.window_handles[1])
        logger.info("Target video opened in new tab")
        
        time.sleep(5)        
        driver = skip_or_watch_ad(driver)
        return driver, watch_duration

# ================================= STRATEGY 2 ============================================== #
""" 
    FUNCTION TO GO TO CHANNEL PAGE, SEARCH THE VIDEO AND WATCH IT
"""
def perform_startegy2(driver, KEY, TARGET_VIDEO_LINK, TARGET_CHANNEL_ELEMENT):
    # get the watch duration
    watch_duration = getWatch_time(TARGET_VIDEO_LINK.get_attribute("href"))
    logger.info(f"Watch duration: {watch_duration}")
    # get the youtube link of the target video
    youtube_url = TARGET_VIDEO_LINK.get_attribute("href")
    logger.info(f"Target video link: {youtube_url}")
    # extract the video id from the youtube link
    target_video_id = re.search(r'(?<=v=)([a-zA-Z0-9_-]{11})', youtube_url).group(1)
    logger.info(f"Target video id: {target_video_id}")
    # open the channel page
    logger.info("Opening the channel page")
    ActionChains(driver).move_to_element(TARGET_CHANNEL_ELEMENT).perform()
    ActionChains(driver).key_down(Keys.CONTROL).click(TARGET_CHANNEL_ELEMENT).key_up(Keys.CONTROL).perform()
    time.sleep(3)
    logger.info("Channel page opened in new tab")
    # switch the driver foucs to the new open tab
    driver.switch_to.window(driver.window_handles[1]);time.sleep(3)
    # click on the videos tab
    currUrl=''; currUrl+=driver.current_url+'/videos'
    driver.get(currUrl)
    
    logger.info("Clicked on the videos tab")
    time.sleep(10)
    # intialize variables for scrolling
    last_index = 0 
    flag=True; videoIDs_found = set()
    
    while flag:
        # get all the video links in the channel page that are visible
        channel_videos = driver.find_elements(By.ID, 'thumbnail')[last_index:]
        channel_videos = list(OrderedDict.fromkeys(channel_videos))
        # iterate through the video links and extract the video id
        for video in channel_videos:
            if len(videoIDs_found)>40:
                errMsg = "No target video found in the channel page within 40 videos"
                logger.info(errMsg)
                PARAMS = {
                    "success": "No",
                    "notes": errMsg,
                    "counter": 0
                }
                send_confimation_to_oracle(driver, KEY, PARAMS)
                driver.quit();exit(0)
            # check if the video link is not None
            if video.get_attribute("href")!=None:
                # extract the video id from the youtube link
                video_id = re.search(r'(?<=v=)([a-zA-Z0-9_-]{11})', video.get_attribute("href")).group(1)
                videoIDs_found.add(video_id)
                logger.info(f"Target: {target_video_id} | Current: {video_id}")
                # check if the video id matches with the target video id
                if video_id == target_video_id:
                    logger.info("Target video found in the channel page")
                    target_videoId_element = video
                    flag=False
                    break
            last_index+=1
        # scroll down the page
        driver.execute_script("window.scrollBy(0, 400);")
    
    if target_videoId_element:
        # get the video into the view
        logger.info("Scrolling to the target video")
        driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", target_videoId_element)
        action = ActionChains(driver)
        action.move_to_element(target_videoId_element).perform()
        action.key_down(Keys.CONTROL).click(target_videoId_element).key_up(Keys.CONTROL).perform();time.sleep(1)
        driver.switch_to.window(driver.window_handles[2])
        logger.info("Target video opened in new tab")
        driver = skip_or_watch_ad(driver)
    else:
        errMsg = "Target video not found in the channel page"
        logger.info(errMsg)
        PARAMS = {
            "success": "No",
            "notes": errMsg,
            "counter": 0
        }
        send_confimation_to_oracle(driver, KEY, PARAMS)
        driver.quit(); exit(0)
    
    return driver, watch_duration

# ================================= STRATEGY 3 ============================================== #
""" 
    FUNCTION TO GO TO MIMICK EXTERNAL TRAFFIC SOURCES
"""
def perform_startegy3(driver, TARGET_VIDEO_LINK, CREDS):
    youtube_url = TARGET_VIDEO_LINK.get_attribute("href")
    target_video_id = re.search(r'(?<=v=)([a-zA-Z0-9_-]{11})', youtube_url).group(1)
    logger.info(f"Target video id: {target_video_id}")
    # List of possible values for UTM parameters
    utm_sources = ["social_media", "referral", "email_marketing", "organic_search", "paid_search", "direct_traffic", "WhatsApp", "Facebook", "LinkedIn"]
    utm_mediums = ["CPC", "CPA", "email_newsletter", "affiliate_marketing", "webinar"]
    utm_campaigns = ["currency_pairs", "trading_signals", "economic_calendar", "forex_education", "managed_accounts"]

    # Generate a random combination
    random_combination = {
        "utm_source": random.choice(utm_sources),
        "utm_medium": random.choice(utm_mediums),
        "utm_campaign": random.choice(utm_campaigns),
    }

    # Construct the YouTube video URL with UTM parameters
    youtube_url = f"https://www.youtube.com/watch?v={target_video_id}&utm_source={random_combination['utm_source']}&utm_medium={random_combination['utm_medium']}&utm_campaign={random_combination['utm_campaign']}"
    logger.info(f"Target video link: {youtube_url}")
    watch_duration = getWatch_time(TARGET_VIDEO_LINK.get_attribute("href"))
    logger.info(f"Watch duration: {watch_duration}")
    # quit the old driver and create a new one
    logger.info("Quitting the old driver")
    driver.quit()
    # get new driver
    logger.info("Getting new driver")
    driver = getDriver(CREDS['PROXY_RACK_DNS'], CREDS['USERNAME'], CREDS['PASSWORD'], with_profile=False)
    # open the external youtube link
    driver.get(youtube_url)
    logger.info("Opened the external youtube link")
    try:
        dialog = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, 'dialog'))
        )
        logger.info("Cookie Banner Found")
        button = dialog.find_element(By.CSS_SELECTOR, 'button[aria-label="Accept the use of cookies and other data for the purposes described"]')
        ActionChains(driver).move_to_element(button).click().perform()
        logger.info("Accept All Clicked")
        time.sleep(2)
        #driver.refresh()
    except:
        logger.info("NO cookie banner found...continuing with the code")
    
    return driver,watch_duration