from loguru import logger
import random
import time

# local imports
from utils_youtubeCTR import *
from strategies import *

# intialize the logger
logger = get_logger()

# get the credentials from oracle
CREDS = getProxy()
# TCREDS = {
#     "KEYWORD": "Top 5 devops certifications",
#     "TARGET_CHANNEL": "Edureka!",
# }
# CREDS.update(TCREDS)
logger.info(f"Target Keyword: {CREDS['KEYWORD']}")
logger.info(f"Target Channel: {CREDS['TARGET_CHANNEL']}")

def perform_ytCTR(withLogin):
    logger.info("Starting the youtube CTR bot")
    # intialize the driver
    if withLogin:
        # intialize the driver with profile if withLogin is True
        logger.info("Since WithLogin is choosen to be True, Logging in to youtube")
        driver = getDriver(CREDS['PROXY_RACK_DNS'], CREDS['USERNAME'], CREDS['PASSWORD'], with_profile=True)
    else:
        # intialize the driver without profile if withLogin is False
        logger.info("Since WithLogin is choosen to be False, Not Logging in to youtube")
        driver = getDriver(CREDS['PROXY_RACK_DNS'], CREDS['USERNAME'], CREDS['PASSWORD'], with_profile=False)
    
    # navigate to youtube homepage
    logger.info("Navigating to youtube homepage")
    driver = navigate_to_youtube(driver,CREDS['UNI_KEY'])
    
    # search for video using the keyword and search for the target channel
    logger.info("Searching for the video")
    driver,targetElements,TARGET_VIDEO_INDEX_COUNTER = search_for_Video(driver, CREDS['UNI_KEY'], CREDS['KEYWORD'], CREDS['TARGET_CHANNEL'])
    
    # choose random strategy to watch the video
    strategy_choice =  random.choice([1,2,3])
    logger.info(f"Strategy chosen: {strategy_choice}")
    if strategy_choice==1:
        driver, watchTime = perform_startegy_1(driver, CREDS['UNI_KEY'], targetElements["TARGET_VIDEO_LINK"], targetElements["PREVIOUS_VIDEO_LINK"])
    
    elif strategy_choice==2:
        driver, watchTime = perform_startegy2(driver, CREDS['UNI_KEY'],targetElements["TARGET_VIDEO_LINK"], targetElements["TARGET_CHANNEL_ELEMENT"])
    
    else:
        driver, watchTime = perform_startegy3(driver, targetElements["TARGET_VIDEO_LINK"], CREDS)
    
    success_notes = ""
    # random like and comment on the video if withLogin is True
    if withLogin and strategy_choice!=3:
        # random like and comment on the video
        driver,likeFlag = random_like_video(driver);time.sleep(random.randint(1, 3)) 
        driver,commentFlag = random_comment_video(driver)
        if likeFlag and commentFlag:
            success_notes = "Watched the video for the specified time, Liked and commented on the video"
        elif likeFlag:
            success_notes = "Watched the video for the specified time, Liked the video"
        elif commentFlag:
            success_notes = "Watched the video for the specified time, Commented on the video"
    
    # wait for the video to finish
    logger.info(f"Waiting for {watchTime} seconds to finish the video")
    time.sleep(watchTime)
    logger.info("Watched the video for the specified time")
    
    if not withLogin or strategy_choice==3:
        success_notes = "Watched the video for the specified time"
    
    success_notes+=f"Strategy Implemented is {strategy_choice}"
    success_notes+=f"; Signed in :{withLogin}"
    PARAMS = {
        'success':"Yes",
        'notes': success_notes,
        'counter': TARGET_VIDEO_INDEX_COUNTER
    }
    send_confimation_to_oracle(driver, CREDS['UNI_KEY'], PARAMS)
    return 

if __name__ == "__main__":
    try:
        signed_prob, unsigned_prob = load_probabilities('config.ini')
        probabilities = [signed_prob, unsigned_prob]
        choice = make_choice(probabilities)
        perform_ytCTR(withLogin=choice)
    except Exception as e:
        logger.error(str(e))
        PARAMS = {
        'success':"No",
        'notes': "internet exception",
        'counter': 0
        }
        send_confimation_to_oracle(None, CREDS['UNI_KEY'], PARAMS)
