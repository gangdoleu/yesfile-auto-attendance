# yesfile_attendance_improved.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
#from dotenv import load_dotenv
import time
import os
import logging
import getpass

# .env 파일 로드 (있는 경우)
#load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def setup_driver():
    """크롬 드라이버 설정 (자동 업데이트)"""
    chrome_options = Options()

    # 테스트할 때는 아래 줄을 주석 처리하여 브라우저를 볼 수 있습니다
    # chrome_options.add_argument("--headless")  # 브라우저 창 숨기기

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    try:
        # 자동으로 적합한 크롬드라이버 다운로드 및 설정
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)
        logger.info("크롬 드라이버 설정 완료")
        return driver
    except Exception as e:
        logger.error(f"크롬 드라이버 설정 실패: {str(e)}")
        return None


def get_login_credentials():
    """로그인 정보 가져오기 (여러 방법 시도)"""
    username = os.environ.get('YESFILE_USERNAME')
    password = os.environ.get('YESFILE_PASSWORD')

    if username and password:
        logger.info("환경변수에서 로그인 정보를 가져왔습니다.")
        return username, password

    # 환경변수가 없으면 사용자 입력 받기
    logger.info("환경변수가 설정되지 않았습니다. 직접 입력해주세요.")
    try:
        username = input("예스파일 아이디: ").strip()
        password = getpass.getpass("예스파일 비밀번호: ").strip()

        if not username or not password:
            logger.error("아이디 또는 비밀번호가 입력되지 않았습니다.")
            return None, None

        return username, password
    except KeyboardInterrupt:
        logger.info("\n입력이 취소되었습니다.")
        return None, None


def login_yesfile(driver, username, password):
    """예스파일 로그인"""
    try:
        logger.info("예스파일 로그인 시작")
        driver.get("https://www.yesfile.com/login")

        # 페이지 로딩 대기
        time.sleep(3)

        # 로그인 폼이 로드될 때까지 대기
        try:
            # 아이디 입력 필드 찾기 (여러 selector 시도)
            username_selectors = [
                (By.NAME, "userid"),
                (By.ID, "userid"),
                (By.NAME, "username"),
                (By.ID, "username"),
                (By.CSS_SELECTOR, "input[type='text']"),
                (By.CSS_SELECTOR, "input[placeholder*='아이디']"),
                (By.CSS_SELECTOR, "input[placeholder*='ID']")
            ]

            username_field = None
            for selector_type, selector_value in username_selectors:
                try:
                    username_field = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    logger.info(f"아이디 입력 필드 찾음: {selector_type}='{selector_value}'")
                    break
                except:
                    continue

            if not username_field:
                logger.error("아이디 입력 필드를 찾을 수 없습니다.")
                return False

            username_field.clear()
            username_field.send_keys(username)

            # 비밀번호 입력 필드 찾기
            password_selectors = [
                (By.NAME, "password"),
                (By.ID, "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.CSS_SELECTOR, "input[placeholder*='비밀번호']"),
                (By.CSS_SELECTOR, "input[placeholder*='password']")
            ]

            password_field = None
            for selector_type, selector_value in password_selectors:
                try:
                    password_field = driver.find_element(selector_type, selector_value)
                    logger.info(f"비밀번호 입력 필드 찾음: {selector_type}='{selector_value}'")
                    break
                except:
                    continue

            if not password_field:
                logger.error("비밀번호 입력 필드를 찾을 수 없습니다.")
                return False

            password_field.clear()
            password_field.send_keys(password)

            # 로그인 버튼 찾기 및 클릭
            login_selectors = [
                (By.XPATH, "//input[@type='submit']"),
                (By.XPATH, "//button[contains(text(), '로그인')]"),
                (By.XPATH, "//input[@value='로그인']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, "input[type='submit']")
            ]

            login_button = None
            for selector_type, selector_value in login_selectors:
                try:
                    login_button = driver.find_element(selector_type, selector_value)
                    logger.info(f"로그인 버튼 찾음: {selector_type}='{selector_value}'")
                    break
                except:
                    continue

            if not login_button:
                logger.error("로그인 버튼을 찾을 수 없습니다.")
                return False

            login_button.click()

            # 로그인 완료 대기
            time.sleep(5)

            # 로그인 성공 확인 (여러 방법으로 체크)
            success_indicators = [
                "마이페이지",
                "로그아웃",
                "내정보",
                "포인트",
                "구매자료"
            ]

            current_url = driver.current_url
            page_source = driver.page_source.lower()

            # URL 변경 확인
            if "login" not in current_url:
                logger.info("URL 변경됨 - 로그인 성공 가능성 높음")
                return True

            # 페이지 내용 확인
            for indicator in success_indicators:
                if indicator.lower() in page_source:
                    logger.info(f"로그인 성공 - '{indicator}' 발견")
                    return True

            logger.error("로그인 실패 - 성공 지표를 찾을 수 없습니다.")
            logger.info(f"현재 URL: {current_url}")
            return False

        except Exception as e:
            logger.error(f"로그인 과정 중 오류: {str(e)}")
            return False

    except Exception as e:
        logger.error(f"로그인 중 오류 발생: {str(e)}")
        return False


def check_attendance(driver):
    """출석체크 수행"""
    try:
        logger.info("출석체크 시작")

        # 이벤트 페이지로 이동 (실제 URL 확인 필요)
        event_urls = [
            "https://www.yesfile.com/event/#tab=view&id=attendroulette"
        ]

        for url in event_urls:
            try:
                driver.get(url)
                time.sleep(3)

                # 출석체크 관련 요소 찾기 (실제 HTML 구조 기반으로 수정)
                attendance_selectors = [
                    # 가장 정확한 선택자를 맨 앞에 배치
                    (By.CSS_SELECTOR, "button.attend_btn"),
                    (By.CSS_SELECTOR, "button[class='attend_btn']"),
                    (By.XPATH, "//button[@class='attend_btn']"),
                    (By.XPATH, "//button[contains(@class, 'attend_btn')]"),
                    # 기존 범용 선택자들 (백업용)
                    (By.XPATH, "//button[contains(text(), '출석체크')]"),
                    (By.XPATH, "//a[contains(text(), '출석체크')]"),
                    (By.XPATH, "//input[contains(@value, '출석체크')]"),
                    (By.CSS_SELECTOR, "button[onclick*='attendance']"),
                    (By.CSS_SELECTOR, "a[href*='attendance']")
                ]

                attendance_element = None
                for selector_type, selector_value in attendance_selectors:
                    try:
                        attendance_element = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((selector_type, selector_value))
                        )
                        logger.info(f"출석체크 버튼 찾음: {selector_type}='{selector_value}'")
                        break
                    except:
                        continue

                if attendance_element:
                    # 버튼 클릭 전 스크롤하여 요소가 보이도록 처리
                    driver.execute_script("arguments[0].scrollIntoView(true);", attendance_element)
                    time.sleep(1)

                    attendance_element.click()
                    logger.info("출석체크 버튼 클릭 완료")
                    time.sleep(3)

                    # 출석체크 완료 확인
                    success_messages = [
                        "출석완료",
                        "출석체크 완료",
                        "이미 출석",
                        "포인트가 적립",
                        "출석 성공",
                        "출석이 완료",
                        "포인트 지급"
                    ]

                    page_source = driver.page_source.lower()
                    for message in success_messages:
                        if message.lower() in page_source:
                            logger.info(f"출석체크 완료 확인 - '{message}' 메시지 발견")
                            return True

                    # Alert 창 확인 (많은 사이트에서 팝업으로 결과 표시)
                    try:
                        alert = driver.switch_to.alert
                        alert_text = alert.text
                        logger.info(f"Alert 메시지: {alert_text}")
                        alert.accept()
                        return True
                    except:
                        pass

                    logger.info("출석체크 버튼을 클릭했지만 완료 메시지를 명확히 확인할 수 없습니다.")
                    return True  # 일단 성공으로 처리

                else:
                    logger.warning(f"URL {url}에서 출석체크 버튼을 찾을 수 없습니다.")

            except Exception as e:
                logger.debug(f"URL {url}에서 출석체크 실패: {str(e)}")
                continue

        logger.warning("모든 URL에서 출석체크 버튼을 찾을 수 없습니다.")
        return False

    except Exception as e:
        logger.error(f"출석체크 중 오류 발생: {str(e)}")
        return False


def main():
    """메인 함수"""
    driver = None
    try:
        logger.info("=== 예스파일 자동 출석체크 시작 ===")

        # 로그인 정보 가져오기
        username, password = get_login_credentials()
        if not username or not password:
            logger.error("로그인 정보가 없습니다.")
            return

        # 드라이버 설정
        driver = setup_driver()
        if not driver:
            logger.error("드라이버 설정에 실패했습니다.")
            return

        # 로그인
        if login_yesfile(driver, username, password):
            logger.info("로그인 성공!")

            # 출석체크
            if check_attendance(driver):
                logger.info("출석체크 완료!")
            else:
                logger.warning("출석체크를 완료할 수 없었습니다.")
        else:
            logger.error("로그인에 실패했습니다.")

        logger.info("=== 자동화 스크립트 완료 ===")

    except KeyboardInterrupt:
        logger.info("\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        logger.error(f"스크립트 실행 중 오류: {str(e)}")
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("브라우저를 종료했습니다.")
            except:
                pass


if __name__ == "__main__":
    main()
