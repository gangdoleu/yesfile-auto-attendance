# yesfile_attendance_improved.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import logging
import getpass
import traceback

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('yesfile_attendance.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_driver():
    """크롬 드라이버 설정 (GitHub Actions 최적화)"""
    chrome_options = Options()
    
    # GitHub Actions 환경 감지
    is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'
    
    if is_github_actions:
        logger.info("GitHub Actions 환경 감지됨 - headless 모드 활성화")
        chrome_options.add_argument("--headless")
    else:
        logger.info("로컬 환경 감지됨 - 브라우저 표시 모드")
        # 로컬 테스트 시에는 headless 모드 비활성화
        
    # 기본 Chrome 옵션
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--start-maximized")
    
    # 봇 탐지 우회 설정 강화
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 추가 안정성 옵션
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")  # 이미지 로딩 비활성화로 속도 향상
    chrome_options.add_argument("--disable-javascript")  # 필요시 제거
    
    try:
        # 자동으로 적합한 크롬드라이버 다운로드 및 설정
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 봇 탐지 우회 JavaScript 실행
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # 타임아웃 설정 (더 긴 대기 시간)
        driver.implicitly_wait(15)
        driver.set_page_load_timeout(30)
        
        logger.info("크롬 드라이버 설정 완료")
        return driver
        
    except Exception as e:
        logger.error(f"크롬 드라이버 설정 실패: {str(e)}")
        logger.error(f"상세 오류: {traceback.format_exc()}")
        return None

def safe_find_element(driver, by, value, timeout=15):
    """안전한 요소 찾기 (강화된 대기 조건)"""
    try:
        logger.debug(f"요소 찾기 시도: {by}='{value}'")
        
        # 요소가 존재하고 상호작용 가능할 때까지 대기
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        
        # 추가 안정성을 위한 대기
        time.sleep(1)
        
        # 요소가 화면에 보이도록 스크롤
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)
        
        logger.debug(f"요소 찾기 성공: {by}='{value}'")
        return element
        
    except TimeoutException:
        logger.debug(f"요소 찾기 실패 (타임아웃): {by}='{value}'")
        return None
    except Exception as e:
        logger.debug(f"요소 찾기 실패: {by}='{value}', 오류: {e}")
        return None

def save_debug_info(driver, prefix="debug"):
    """디버깅 정보 저장"""
    try:
        # 스크린샷 저장
        screenshot_path = f"{prefix}_screenshot.png"
        driver.save_screenshot(screenshot_path)
        logger.info(f"스크린샷 저장: {screenshot_path}")
        
        # HTML 소스 저장
        html_path = f"{prefix}_page_source.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info(f"HTML 소스 저장: {html_path}")
        
        # 현재 URL 로깅
        logger.info(f"현재 URL: {driver.current_url}")
        
        # 모든 input 요소 정보 수집
        try:
            inputs = driver.find_elements(By.TAG_NAME, "input")
            logger.info(f"페이지의 input 요소 개수: {len(inputs)}")
            for i, inp in enumerate(inputs[:10]):  # 처음 10개만 로깅
                name_attr = inp.get_attribute('name')
                type_attr = inp.get_attribute('type')
                id_attr = inp.get_attribute('id')
                class_attr = inp.get_attribute('class')
                logger.debug(f"Input {i}: name='{name_attr}', type='{type_attr}', id='{id_attr}', class='{class_attr}'")
        except Exception as e:
            logger.warning(f"Input 요소 분석 실패: {e}")
            
    except Exception as e:
        logger.warning(f"디버깅 정보 저장 실패: {e}")

def get_login_credentials():
    """로그인 정보 가져오기"""
    username = os.environ.get('YESFILE_USERNAME')
    password = os.environ.get('YESFILE_PASSWORD')

    if username and password:
        logger.info("환경변수에서 로그인 정보를 가져왔습니다.")
        return username, password

    # GitHub Actions 환경에서는 사용자 입력 불가
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        logger.error("GitHub Actions 환경에서 환경변수가 설정되지 않았습니다.")
        return None, None

    # 로컬 환경에서만 사용자 입력 받기
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
    """예스파일 로그인 (강화된 버전)"""
    try:
        logger.info("예스파일 로그인 시작")
        
        # 로그인 페이지로 이동
        login_url = "https://www.yesfile.com/login"
        logger.info(f"로그인 페이지 접속: {login_url}")
        driver.get(login_url)
        
        # 페이지 로딩 대기
        time.sleep(5)
        
        # 디버깅 정보 저장
        save_debug_info(driver, "login_page")
        
        # 아이디 입력 필드 찾기 (더 많은 선택자 시도)
        username_selectors = [
            (By.NAME, "userid"),
            (By.ID, "userid"),
            (By.NAME, "username"),
            (By.ID, "username"),
            (By.NAME, "user_id"),
            (By.ID, "user_id"),
            (By.CSS_SELECTOR, "input[name='userid']"),
            (By.CSS_SELECTOR, "input[id='userid']"),
            (By.CSS_SELECTOR, "input[type='text'][name*='user']"),
            (By.CSS_SELECTOR, "input[type='text'][placeholder*='아이디']"),
            (By.CSS_SELECTOR, "input[type='text'][placeholder*='ID']"),
            (By.XPATH, "//input[@type='text' and contains(@placeholder, '아이디')]"),
            (By.XPATH, "//input[@type='text' and contains(@name, 'user')]")
        ]

        username_field = None
        for selector_type, selector_value in username_selectors:
            username_field = safe_find_element(driver, selector_type, selector_value, timeout=10)
            if username_field:
                logger.info(f"아이디 입력 필드 찾음: {selector_type}='{selector_value}'")
                break

        if not username_field:
            logger.error("아이디 입력 필드를 찾을 수 없습니다.")
            save_debug_info(driver, "username_field_not_found")
            return False

        # 아이디 입력
        try:
            username_field.clear()
            time.sleep(0.5)
            username_field.send_keys(username)
            logger.info("아이디 입력 완료")
        except Exception as e:
            logger.error(f"아이디 입력 실패: {e}")
            return False

        # 비밀번호 입력 필드 찾기 (더 강화된 대기 조건)
        password_selectors = [
            (By.NAME, "password"),
            (By.ID, "password"),
            (By.NAME, "passwd"),
            (By.ID, "passwd"),
            (By.NAME, "pwd"),
            (By.ID, "pwd"),
            (By.CSS_SELECTOR, "input[name='password']"),
            (By.CSS_SELECTOR, "input[id='password']"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.CSS_SELECTOR, "input[type='password'][name*='pass']"),
            (By.XPATH, "//input[@type='password']"),
            (By.XPATH, "//input[@type='password' and contains(@name, 'pass')]")
        ]

        # 비밀번호 필드 찾기 전 추가 대기
        time.sleep(2)
        
        password_field = None
        for selector_type, selector_value in password_selectors:
            password_field = safe_find_element(driver, selector_type, selector_value, timeout=10)
            if password_field:
                logger.info(f"비밀번호 입력 필드 찾음: {selector_type}='{selector_value}'")
                break

        if not password_field:
            logger.error("비밀번호 입력 필드를 찾을 수 없습니다.")
            save_debug_info(driver, "password_field_not_found")
            return False

        # 비밀번호 입력
        try:
            password_field.clear()
            time.sleep(0.5)
            password_field.send_keys(password)
            logger.info("비밀번호 입력 완료")
        except Exception as e:
            logger.error(f"비밀번호 입력 실패: {e}")
            return False

        # 로그인 버튼 찾기 및 클릭
        login_selectors = [
            (By.XPATH, "//input[@type='submit' and @value='로그인']"),
            (By.XPATH, "//button[contains(text(), '로그인')]"),
            (By.XPATH, "//input[@value='로그인']"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.CSS_SELECTOR, "input[type='submit']"),
            (By.XPATH, "//form//input[@type='submit']"),
            (By.XPATH, "//form//button[@type='submit']")
        ]

        login_button = None
        for selector_type, selector_value in login_selectors:
            login_button = safe_find_element(driver, selector_type, selector_value, timeout=5)
            if login_button:
                logger.info(f"로그인 버튼 찾음: {selector_type}='{selector_value}'")
                break

        if not login_button:
            logger.error("로그인 버튼을 찾을 수 없습니다.")
            save_debug_info(driver, "login_button_not_found")
            return False

        # 로그인 버튼 클릭
        try:
            login_button.click()
            logger.info("로그인 버튼 클릭 완료")
        except Exception as e:
            logger.error(f"로그인 버튼 클릭 실패: {e}")
            return False

        # 로그인 처리 대기
        time.sleep(7)

        # 로그인 결과 확인
        save_debug_info(driver, "after_login")
        
        # 로그인 성공 확인 (다양한 방법으로 체크)
        success_indicators = [
            "마이페이지", "로그아웃", "내정보", "포인트", "구매자료",
            "mypage", "logout", "point", "profile"
        ]

        current_url = driver.current_url.lower()
        page_source = driver.page_source.lower()

        # URL 변경 확인
        if "login" not in current_url or "main" in current_url or "index" in current_url:
            logger.info("URL 변경됨 - 로그인 성공 가능성 높음")
            
            # 페이지 내용으로 재확인
            for indicator in success_indicators:
                if indicator.lower() in page_source:
                    logger.info(f"로그인 성공 확인 - '{indicator}' 발견")
                    return True
            
            # URL이 변경되었다면 일단 성공으로 처리
            logger.info("URL 변경으로 로그인 성공으로 판단")
            return True

        # 현재 페이지에서 성공 지표 확인
        for indicator in success_indicators:
            if indicator.lower() in page_source:
                logger.info(f"로그인 성공 - '{indicator}' 발견")
                return True

        # 로그인 실패 메시지 확인
        error_indicators = [
            "로그인 실패", "아이디를 확인", "비밀번호를 확인", "login failed",
            "잘못된", "존재하지 않는", "invalid", "incorrect"
        ]
        
        for error in error_indicators:
            if error.lower() in page_source:
                logger.error(f"로그인 실패 - '{error}' 오류 메시지 발견")
                return False

        logger.warning("로그인 결과를 명확히 판단할 수 없습니다.")
        logger.info(f"현재 URL: {current_url}")
        return False

    except Exception as e:
        logger.error(f"로그인 중 오류 발생: {str(e)}")
        logger.error(f"상세 오류: {traceback.format_exc()}")
        save_debug_info(driver, "login_error")
        return False

def check_attendance(driver):
    """출석체크 수행 (강화된 버전)"""
    try:
        logger.info("출석체크 시작")

        # 이벤트 페이지 URL들 (실제 URL 확인 필요)
        event_urls = [
            "https://www.yesfile.com/event/#tab=view&id=attendroulette",
            "https://www.yesfile.com/event/attendance",
            "https://www.yesfile.com/event",
            "https://www.yesfile.com/attendance"
        ]

        for url in event_urls:
            try:
                logger.info(f"이벤트 페이지 접속 시도: {url}")
                driver.get(url)
                time.sleep(5)
                
                save_debug_info(driver, f"event_page_{event_urls.index(url)}")

                # 출석체크 관련 요소 찾기
                attendance_selectors = [
                    # 가장 구체적인 선택자부터
                    (By.CSS_SELECTOR, "button.attend_btn"),
                    (By.CSS_SELECTOR, "button[class*='attend']"),
                    (By.CSS_SELECTOR, "a.attend_btn"),
                    (By.CSS_SELECTOR, "a[class*='attend']"),
                    (By.XPATH, "//button[@class='attend_btn']"),
                    (By.XPATH, "//button[contains(@class, 'attend')]"),
                    (By.XPATH, "//a[contains(@class, 'attend')]"),
                    # 텍스트 기반 선택자
                    (By.XPATH, "//button[contains(text(), '출석체크')]"),
                    (By.XPATH, "//a[contains(text(), '출석체크')]"),
                    (By.XPATH, "//button[contains(text(), '출석')]"),
                    (By.XPATH, "//a[contains(text(), '출석')]"),
                    (By.XPATH, "//input[contains(@value, '출석체크')]"),
                    (By.XPATH, "//input[contains(@value, '출석')]"),
                    # 일반적인 선택자
                    (By.CSS_SELECTOR, "button[onclick*='attendance']"),
                    (By.CSS_SELECTOR, "a[href*='attendance']"),
                    (By.CSS_SELECTOR, "button[onclick*='attend']"),
                    (By.CSS_SELECTOR, "a[href*='attend']")
                ]

                attendance_element = None
                for selector_type, selector_value in attendance_selectors:
                    attendance_element = safe_find_element(driver, selector_type, selector_value, timeout=5)
                    if attendance_element:
                        logger.info(f"출석체크 버튼 찾음: {selector_type}='{selector_value}'")
                        break

                if attendance_element:
                    try:
                        # 버튼 클릭
                        attendance_element.click()
                        logger.info("출석체크 버튼 클릭 완료")
                        time.sleep(5)

                        save_debug_info(driver, "after_attendance_click")

                        # 출석체크 완료 확인
                        success_messages = [
                            "출석완료", "출석체크 완료", "이미 출석", "포인트가 적립",
                            "출석 성공", "출석이 완료", "포인트 지급", "출석체크가 완료",
                            "출석 처리", "출석했습니다", "attendance complete"
                        ]

                        page_source = driver.page_source.lower()
                        for message in success_messages:
                            if message.lower() in page_source:
                                logger.info(f"출석체크 완료 확인 - '{message}' 메시지 발견")
                                return True

                        # Alert 창 확인
                        try:
                            WebDriverWait(driver, 3).until(EC.alert_is_present())
                            alert = driver.switch_to.alert
                            alert_text = alert.text
                            logger.info(f"Alert 메시지: {alert_text}")
                            alert.accept()
                            
                            # Alert 메시지로 성공 여부 판단
                            for message in success_messages:
                                if message.lower() in alert_text.lower():
                                    logger.info("Alert에서 출석체크 완료 확인")
                                    return True
                                    
                        except TimeoutException:
                            logger.debug("Alert 창이 없습니다.")
                        except Exception as e:
                            logger.debug(f"Alert 처리 중 오류: {e}")

                        logger.info("출석체크 버튼을 클릭했지만 완료 메시지를 명확히 확인할 수 없습니다.")
                        return True  # 클릭은 성공했으므로 일단 성공으로 처리

                    except Exception as e:
                        logger.error(f"출석체크 버튼 클릭 실패: {e}")
                        continue
                else:
                    logger.debug(f"URL {url}에서 출석체크 버튼을 찾을 수 없습니다.")

            except Exception as e:
                logger.debug(f"URL {url}에서 출석체크 시도 실패: {str(e)}")
                continue

        logger.warning("모든 URL에서 출석체크 버튼을 찾을 수 없습니다.")
        return False

    except Exception as e:
        logger.error(f"출석체크 중 오류 발생: {str(e)}")
        logger.error(f"상세 오류: {traceback.format_exc()}")
        save_debug_info(driver, "attendance_error")
        return False

def main():
    """메인 함수"""
    driver = None
    try:
        logger.info("=== 예스파일 자동 출석체크 시작 ===")
        logger.info(f"실행 환경: {'GitHub Actions' if os.environ.get('GITHUB_ACTIONS') else '로컬'}")

        # 로그인 정보 가져오기
        username, password = get_login_credentials()
        if not username or not password:
            logger.error("로그인 정보가 없습니다.")
            return False

        # 드라이버 설정
        driver = setup_driver()
        if not driver:
            logger.error("드라이버 설정에 실패했습니다.")
            return False

        # 로그인
        if login_yesfile(driver, username, password):
            logger.info("로그인 성공!")

            # 출석체크
            if check_attendance(driver):
                logger.info("출석체크 완료!")
                return True
            else:
                logger.warning("출석체크를 완료할 수 없었습니다.")
                return False
        else:
            logger.error("로그인에 실패했습니다.")
            return False

    except KeyboardInterrupt:
        logger.info("\n사용자에 의해 중단되었습니다.")
        return False
    except Exception as e:
        logger.error(f"스크립트 실행 중 오류: {str(e)}")
        logger.error(f"상세 오류: {traceback.format_exc()}")
        return False
    finally:
        logger.info("=== 자동화 스크립트 완료 ===")
        if driver:
            try:
                driver.quit()
                logger.info("브라우저를 종료했습니다.")
            except:
                pass

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
