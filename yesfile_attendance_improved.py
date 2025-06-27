# yesfile_attendance_final.py (최종 수정 버전)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
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
    """크롬 드라이버 설정 (JavaScript 활성화)"""
    chrome_options = Options()
    
    # GitHub Actions 환경 감지
    is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'
    
    if is_github_actions:
        logger.info("GitHub Actions 환경 감지됨 - headless 모드 활성화")
        chrome_options.add_argument("--headless")
    else:
        logger.info("로컬 환경 감지됨 - 브라우저 표시 모드")
        
    # 기본 Chrome 옵션 (JavaScript 활성화)
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
    
    # 추가 안정성 옵션 (JavaScript는 활성화 상태 유지)
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")  # 속도 향상
    # --disable-javascript 옵션 제거됨 (이것이 핵심!)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 봇 탐지 우회 JavaScript 실행
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # 타임아웃 설정
        driver.implicitly_wait(20)  # 더 긴 대기 시간
        driver.set_page_load_timeout(40)
        
        logger.info("크롬 드라이버 설정 완료 (JavaScript 활성화)")
        return driver
        
    except Exception as e:
        logger.error(f"크롬 드라이버 설정 실패: {str(e)}")
        logger.error(f"상세 오류: {traceback.format_exc()}")
        return None

def safe_find_element(driver, by, value, timeout=20):
    """안전한 요소 찾기 (더 긴 대기 시간)"""
    try:
        logger.debug(f"요소 찾기 시도: {by}='{value}'")
        
        # 요소가 존재하고 상호작용 가능할 때까지 대기
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        
        # JavaScript 실행 완료 대기
        time.sleep(2)
        
        # 요소가 화면에 보이도록 스크롤
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(1)
        
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
        
        # JavaScript 로드 확인
        try:
            js_enabled = driver.execute_script("return typeof jQuery !== 'undefined' || document.readyState === 'complete';")
            logger.info(f"JavaScript 실행 상태: {js_enabled}")
        except:
            logger.warning("JavaScript 실행 상태를 확인할 수 없습니다.")
        
        # 모든 버튼과 폼 요소 정보 수집
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            inputs = driver.find_elements(By.TAG_NAME, "input")
            forms = driver.find_elements(By.TAG_NAME, "form")
            
            logger.info(f"페이지 요소 개수 - 버튼: {len(buttons)}, Input: {len(inputs)}, Form: {len(forms)}")
            
            # 각 버튼의 세부 정보
            for i, btn in enumerate(buttons[:5]):  # 처음 5개만
                text = btn.text.strip()
                onclick = btn.get_attribute('onclick')
                btn_type = btn.get_attribute('type')
                btn_id = btn.get_attribute('id')
                btn_class = btn.get_attribute('class')
                logger.debug(f"Button {i}: text='{text}', type='{btn_type}', id='{btn_id}', class='{btn_class}', onclick='{onclick}'")
                
        except Exception as e:
            logger.warning(f"요소 분석 실패: {e}")
            
    except Exception as e:
        logger.warning(f"디버깅 정보 저장 실패: {e}")

def get_login_credentials():
    """로그인 정보 가져오기"""
    username = os.environ.get('YESFILE_USERNAME')
    password = os.environ.get('YESFILE_PASSWORD')

    if username and password:
        logger.info("환경변수에서 로그인 정보를 가져왔습니다.")
        return username, password

    if os.environ.get('GITHUB_ACTIONS') == 'true':
        logger.error("GitHub Actions 환경에서 환경변수가 설정되지 않았습니다.")
        return None, None

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
    """예스파일 로그인 (폼 제출 방식 개선)"""
    try:
        logger.info("예스파일 로그인 시작")
        
        # 로그인 페이지로 이동
        login_url = "https://www.yesfile.com/login"
        logger.info(f"로그인 페이지 접속: {login_url}")
        driver.get(login_url)
        
        # 페이지 로딩 완료 대기 (JavaScript 실행 포함)
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # 추가 JavaScript 로딩 대기
        time.sleep(7)
        
        # 디버깅 정보 저장
        save_debug_info(driver, "login_page_with_js")
        
        # 아이디 입력 필드 찾기
        username_selectors = [
            (By.NAME, "userid"),
            (By.ID, "userid"),
            (By.NAME, "username"),
            (By.ID, "username"),
            (By.CSS_SELECTOR, "input[name='userid']"),
            (By.CSS_SELECTOR, "input[type='text'][name*='user']"),
            (By.XPATH, "//input[@type='text' and contains(@name, 'user')]")
        ]

        username_field = None
        for selector_type, selector_value in username_selectors:
            username_field = safe_find_element(driver, selector_type, selector_value, timeout=15)
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
            time.sleep(1)
            username_field.send_keys(username)
            logger.info("아이디 입력 완료")
        except Exception as e:
            logger.error(f"아이디 입력 실패: {e}")
            return False

        # 비밀번호 입력 필드 찾기
        password_selectors = [
            (By.NAME, "password"),
            (By.ID, "password"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.CSS_SELECTOR, "input[name='password']"),
            (By.XPATH, "//input[@type='password']")
        ]

        password_field = None
        for selector_type, selector_value in password_selectors:
            password_field = safe_find_element(driver, selector_type, selector_value, timeout=15)
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
            time.sleep(1)
            password_field.send_keys(password)
            logger.info("비밀번호 입력 완료")
        except Exception as e:
            logger.error(f"비밀번호 입력 실패: {e}")
            return False

        # === 새로운 로그인 제출 방식 (복수 시도) ===
        login_success = False
        
        # 방법 1: Enter 키로 폼 제출
        try:
            logger.info("Enter 키로 로그인 시도")
            password_field.send_keys(Keys.RETURN)
            time.sleep(5)
            
            # 로그인 결과 확인
            if check_login_success(driver):
                logger.info("Enter 키 로그인 성공")
                return True
        except Exception as e:
            logger.warning(f"Enter 키 로그인 실패: {e}")

        # 방법 2: 폼을 직접 찾아서 제출
        try:
            logger.info("폼 직접 제출 시도")
            form_element = driver.find_element(By.TAG_NAME, "form")
            if form_element:
                driver.execute_script("arguments[0].submit();", form_element)
                time.sleep(5)
                
                if check_login_success(driver):
                    logger.info("폼 직접 제출 로그인 성공")
                    return True
        except Exception as e:
            logger.warning(f"폼 직접 제출 실패: {e}")

        # 방법 3: JavaScript로 로그인 함수 직접 호출
        try:
            logger.info("JavaScript 로그인 함수 호출 시도")
            # 일반적인 로그인 함수명들 시도
            js_functions = [
                "submitForm()",
                "loginSubmit()",
                "doLogin()",
                "userLogin()",
                "memberLogin()",
                "login()"
            ]
            
            for js_func in js_functions:
                try:
                    driver.execute_script(js_func)
                    time.sleep(3)
                    if check_login_success(driver):
                        logger.info(f"JavaScript 함수 {js_func} 로그인 성공")
                        return True
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"JavaScript 로그인 함수 호출 실패: {e}")

        # 방법 4: 로그인 버튼 찾기 (기존 방식)
        try:
            logger.info("로그인 버튼 찾기 시도")
            login_selectors = [
                (By.XPATH, "//button[contains(text(), '로그인')]"),
                (By.XPATH, "//input[@value='로그인']"),
                (By.XPATH, "//input[@type='submit']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, "input[type='submit']"),
                (By.XPATH, "//button[contains(@onclick, 'login')]"),
                (By.XPATH, "//input[contains(@onclick, 'login')]")
            ]

            for selector_type, selector_value in login_selectors:
                login_button = safe_find_element(driver, selector_type, selector_value, timeout=5)
                if login_button:
                    logger.info(f"로그인 버튼 찾음: {selector_type}='{selector_value}'")
                    login_button.click()
                    time.sleep(5)
                    
                    if check_login_success(driver):
                        logger.info("로그인 버튼 클릭 성공")
                        return True
                    break
        except Exception as e:
            logger.warning(f"로그인 버튼 방식 실패: {e}")

        # 모든 방법 실패
        logger.error("모든 로그인 방법이 실패했습니다.")
        save_debug_info(driver, "all_login_methods_failed")
        return False

    except Exception as e:
        logger.error(f"로그인 중 오류 발생: {str(e)}")
        logger.error(f"상세 오류: {traceback.format_exc()}")
        save_debug_info(driver, "login_error")
        return False

def check_login_success(driver):
    """로그인 성공 여부 확인"""
    try:
        current_url = driver.current_url.lower()
        page_source = driver.page_source.lower()

        # 로그인 성공 지표들
        success_indicators = [
            "마이페이지", "로그아웃", "내정보", "포인트", "구매자료",
            "mypage", "logout", "point", "profile", "dashboard"
        ]

        # URL 변경 확인
        if "login" not in current_url:
            logger.info("로그인 페이지에서 벗어남 - 성공 가능성")
            
        # 페이지 내용 확인
        for indicator in success_indicators:
            if indicator.lower() in page_source:
                logger.info(f"로그인 성공 지표 발견: '{indicator}'")
                return True
        
        # 실패 지표 확인
        error_indicators = [
            "로그인 실패", "아이디를 확인", "비밀번호를 확인", "login failed"
        ]
        
        for error in error_indicators:
            if error.lower() in page_source:
                logger.warning(f"로그인 실패 지표 발견: '{error}'")
                return False

        # 명확하지 않은 경우
        if "login" not in current_url:
            logger.info("URL 변경 기준으로 로그인 성공으로 판단")
            return True
            
        return False
        
    except Exception as e:
        logger.warning(f"로그인 성공 여부 확인 실패: {e}")
        return False

def check_attendance(driver):
    """출석체크 수행"""
    try:
        logger.info("출석체크 시작")

        # 이벤트 페이지 URL들
        event_urls = [
            "https://www.yesfile.com/event/#tab=view&id=attendroulette",
            "https://www.yesfile.com/event/attendance",
            "https://www.yesfile.com/event",
            "https://www.yesfile.com/"
        ]

        for url in event_urls:
            try:
                logger.info(f"이벤트 페이지 접속: {url}")
                driver.get(url)
                
                # JavaScript 로딩 완료 대기
                WebDriverWait(driver, 15).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                time.sleep(5)
                
                save_debug_info(driver, f"event_page_{event_urls.index(url)}")

                # 출석체크 버튼 찾기
                attendance_selectors = [
                    (By.CSS_SELECTOR, "button.attend_btn"),
                    (By.CSS_SELECTOR, "button[class*='attend']"),
                    (By.XPATH, "//button[contains(text(), '출석체크')]"),
                    (By.XPATH, "//button[contains(text(), '출석')]"),
                    (By.XPATH, "//a[contains(text(), '출석체크')]"),
                    (By.XPATH, "//a[contains(text(), '출석')]"),
                    (By.CSS_SELECTOR, "a[href*='attendance']"),
                    (By.CSS_SELECTOR, "button[onclick*='attendance']")
                ]

                for selector_type, selector_value in attendance_selectors:
                    attendance_element = safe_find_element(driver, selector_type, selector_value, timeout=5)
                    if attendance_element:
                        logger.info(f"출석체크 버튼 찾음: {selector_type}='{selector_value}'")
                        attendance_element.click()
                        time.sleep(5)

                        # 출석체크 완료 확인
                        page_source = driver.page_source.lower()
                        success_messages = [
                            "출석완료", "출석체크 완료", "이미 출석", "포인트가 적립",
                            "attendance complete", "출석 성공"
                        ]

                        for message in success_messages:
                            if message.lower() in page_source:
                                logger.info(f"출석체크 완료: '{message}'")
                                return True

                        logger.info("출석체크 버튼 클릭 완료 (결과 확인 중)")
                        return True

            except Exception as e:
                logger.debug(f"URL {url}에서 출석체크 실패: {e}")
                continue

        logger.warning("출석체크 버튼을 찾을 수 없습니다.")
        return False

    except Exception as e:
        logger.error(f"출석체크 중 오류: {str(e)}")
        return False

def main():
    """메인 함수"""
    driver = None
    try:
        logger.info("=== 예스파일 자동 출석체크 시작 (JavaScript 활성화) ===")
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
