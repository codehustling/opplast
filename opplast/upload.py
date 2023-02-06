from .constants import *
from .logging import Log
from .exceptions import *

from pathlib import Path
from typing import Tuple, Optional, Union
from time import sleep

from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver import FirefoxOptions, FirefoxProfile

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_path(file_path: str) -> str:
    # no clue why, but this character gets added for me when running
    return str(Path(file_path)).replace("\u202a", "")


class Upload:
    def _init_(
        self,
        profile: Union[str, FirefoxProfile],
        executable_path: str = "geckodriver",
        timeout: int = 3,
        headless: bool = True,
        debug: bool = True,
        options: FirefoxOptions = webdriver.FirefoxOptions(),
    ) -> None:
        if isinstance(profile, str):
            profile = webdriver.FirefoxProfile(profile)

        options.headless = headless
        options.binary_location = r'/usr/bin/firefox-esr'
        self.driver = webdriver.Firefox(
            firefox_profile=profile, options=options
        )
        self.timeout = timeout
        self.log = Log(debug)

        self.log.debug("Firefox is now running")

    def click(self, element):
        element.click()
        sleep(self.timeout)
        return element

    def send(self, element, text: str) -> None:
        element.clear()
        sleep(self.timeout)
        element.send_keys(text)
        sleep(self.timeout)

    def click_next(self, modal) -> None:
        modal.find_element_by_id(NEXT_BUTTON).click()
        sleep(self.timeout)

    def not_uploaded(self, modal) -> bool:
        return modal.find_element_by_xpath(STATUS_CONTAINER).text.find(UPLOADED) != -1

    def upload(
        self,
        file: str,
        title: str = "",
        description: str = "",
        thumbnail: str = "",
        tags: list = [],
        only_upload: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """Uploads a video to YouTube.
        Returns if the video was uploaded and the video id.
        """
        if not file:
            raise FileNotFoundError(f'Could not find file with path: "{file}"')
        # channel_no=channelid
        channel_no = 1
        self.driver.get("https://www.youtube.com/channel_switcher?next=%2Faccount&feature=settings")
        xpath_for_channel=f"/html/body/ytd-app/div[{channel_no}]/ytd-page-manager/ytd-browse/ytd-two-column-browse-results-renderer/div[1]/ytd-section-list-renderer/div[2]/ytd-item-section-renderer/div[3]/ytd-channel-switcher-page-renderer/div[2]/div[2]/ytd-account-item-renderer[1]/tp-yt-paper-icon-item"
        WebDriverWait(self.driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, xpath_for_channel)))
        self.driver.find_element_by_xpath(xpath_for_channel).click()
        self.driver.get(YOUTUBE_UPLOAD_URL)
        sleep(self.timeout)
        try:
            temp =  self.driver.find_element_by_xpath(f"/html/body/ytcp-warm-welcome-dialog/ytcp-dialog/tp-yt-paper-dialog/div[2]/div/ytcp-button")
            temp.click()
            print("Try block")
        except Exception as e:
            print(e)



        self.log.debug(f'Trying to upload "{file}" to YouTube...')

        self.driver.find_element_by_xpath(INPUT_FILE_VIDEO).send_keys(get_path(file))
        sleep(self.timeout)

        modal = self.driver.find_element_by_css_selector(UPLOAD_DIALOG_MODAL)
        self.log.debug("Found YouTube upload Dialog Modal")

        if only_upload:
            video_id = self.get_video_id(modal)

            while self.not_uploaded(modal):
                self.log.debug("Still uploading...")
                sleep(self.timeout)

            return True, video_id

        self.log.debug(f'Trying to set "{title}" as title...')
        sleep(self.timeout)
        try:

            self.driver.find_element_by_xpath("/html/body/ytcp-auth-confirmation-dialog/ytcp-confirmation-dialog/ytcp-dialog/tp-yt-paper-dialog/div[3]/div[2]/ytcp-button[2]/div").click()
            sleep(self.timeout)
            self.driver.find_element_by_xpath("/html/body/div[1]/div[1]/div[2]/div/div[2]/div/div/div[2]/div/div[1]/div/form/span/section/div/div/div[2]/div[1]/div/div/div/div/div[1]/div/div[1]/input").sendkeys("Mai_San987**")
            import org.openqa.selenium.Keys

            self.driver.find_element_by_xpath("/html/body/div[1]/div[1]/div[2]/div/div[2]/div/div/div[2]/div/div[1]/div/form/span/section/div/div/div[2]/div[1]/div/div/div/div/div[1]/div/div[1]/input").sendKeys(Keys.RETURN)
        except Exception as e:
            print(e)    

        # TITLE
        title_field = self.click(modal.find_element_by_id(TEXTBOX))

        # get file name (default) title
        title = title if title else title_field.text

        if len(title) > TITLE_COUNTER:
            raise ExceedsCharactersAllowed(
                f"Title was not set due to exceeding the maximum allowed characters ({len(title)}/{TITLE_COUNTER})"
            )

        # clearing out title which defaults to filename
        for _ in range(len(title_field.text) + 10):
            # more backspaces than needed just to be sure
            title_field.send_keys(Keys.BACKSPACE)
            sleep(0.1)

        self.send(title_field, title)

        if description:
            if len(description) > DESCRIPTION_COUNTER:
                raise ExceedsCharactersAllowed(
                    f"Description was not set due to exceeding the maximum allowed characters ({len(description)}/{DESCRIPTION_COUNTER})"
                )

            self.log.debug(f'Trying to set "{description}" as description...')
            container = modal.find_element_by_xpath(DESCRIPTION_CONTAINER)
            description_field = self.click(container.find_element_by_id(TEXTBOX))

            self.send(description_field, description)

        if thumbnail:
            self.log.debug(f'Trying to set "{thumbnail}" as thumbnail...')
            modal.find_element_by_xpath(INPUT_FILE_THUMBNAIL).send_keys(
                get_path(thumbnail)
            )
            sleep(self.timeout)

        self.log.debug('Trying to set video to "Not made for kids"...')

        kids_section = modal.find_element_by_name(NOT_MADE_FOR_KIDS_LABEL)
        kids_section.find_element_by_id(RADIO_LABEL).click()
        sleep(self.timeout)

        if tags:
            self.click(modal.find_element_by_xpath(MORE_OPTIONS_CONTAINER))

            tags = ",".join(str(tag) for tag in tags)

            if len(tags) > TAGS_COUNTER:
                raise ExceedsCharactersAllowed(
                    f"Tags were not set due to exceeding the maximum allowed characters ({len(tags)}/{TAGS_COUNTER})"
                )

            self.log.debug(f'Trying to set "{tags}" as tags...')
            container = modal.find_element_by_xpath(TAGS_CONTAINER)
            tags_field = self.click(container.find_element_by_id(TEXT_INPUT))
            self.send(tags_field, tags)

        # sometimes you have 4 tabs instead of 3
        # this handles both cases
        for _ in range(3):
            try:
                self.click_next(modal)
            except:
                pass

        self.log.debug("Trying to set video visibility to public...")
        public_main_button = modal.find_element_by_name(PUBLIC_BUTTON)
        public_main_button.find_element_by_id(RADIO_LABEL).click()
        video_id = self.get_video_id(modal)

        while self.not_uploaded(modal):
            self.log.debug("Still uploading...")
            sleep(1)

        done_button = modal.find_element_by_id(DONE_BUTTON)

        if done_button.get_attribute("aria-disabled") == "true":
            self.log.debug(self.driver.find_element_by_xpath(ERROR_CONTAINER).text)
            return False, None

        self.click(done_button)

        return True, video_id

    def get_video_id(self, modal) -> Optional[str]:
        video_id = None
        try:
            video_url_container = modal.find_element_by_xpath(VIDEO_URL_CONTAINER)
            video_url_element = video_url_container.find_element_by_xpath(
                VIDEO_URL_ELEMENT
            )

            video_id = video_url_element.get_attribute(HREF).split("/")[-1]
        except:
            raise VideoIDError("Could not get video ID")

        return video_id

    def close(self):
        self.driver.quit()
        self.log.debug("Closed Firefox")
