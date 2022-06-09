from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import time
from sys import exit
import os
import pandas as pd
from win10toast import ToastNotifier


def check_today():
    df = pd.read_csv('logging.log', names=[
        'date', 'time', 'text', 'status'])
    date = time.strftime("%a %b %d", time.localtime())
    return 0 in df[df['date'] == date]['status'].values


class Registrant():
    def __init__(self, driver_kind='Edge', url="", silent=True, alert=True, alert_time=3, timeout=10, student_ID=None, password=None):
        '''
        # Parameters
        student_ID & password : you can also use Registrant().set_ID_password() to set

        driver_kind : {'Edge', 'Firefox', 'Chrome'}, default='Edge'

        silent : bool, default=True
            Not to open the browser window
        '''
        self.student_ID = student_ID
        self.password = password
        self.silent = silent
        self.url = url
        self.alert = alert
        self.alert_time = alert_time
        self.timeout = timeout
        self.driver = None

        if check_today():
            self.printExit('今日已填报', 0)

        if driver_kind == 'Firefox':
            self.options = webdriver.FirefoxOptions()
            self.initOptions()
            self.driver = webdriver.Firefox(options=self.options)
        elif driver_kind == 'Chrome':
            self.options = webdriver.ChromeOptions()
            self.initOptions()
            self.driver = webdriver.Chrome(options=self.options)
        elif driver_kind == 'Edge':
            self.options = webdriver.EdgeOptions()
            # self.initOptions()
            self.driver = webdriver.Edge(options=self.options)
            if self.silent:
                self.driver.set_window_rect(0,-2000)
        else:
            raise ValueError

    def initOptions(self):
        '''
        浏览器启动参数
        '''
        self.options.headless = self.silent
        self.options.add_argument('--disable-images')

    def set_ID_password(self, student_ID=None, password=None):
        self.student_ID = student_ID
        self.password = password

    def printExit(self, text, ex=0):
        if self.alert and ex == 0 or ex == 1:
            toaster = ToastNotifier()
            toaster.show_toast("Registrant",
                               text,
                               duration=self.alert_time)
        if self.driver:
            self.driver.quit()
        logging_content = time.strftime("%a %b %d,%H:%M:%S",
                                        time.localtime())+','+text+','+str(ex)+'\n'
        print(logging_content)
        with open('logging.log', 'a', encoding='utf-8') as file:
            file.write(logging_content)
        exit(ex)

    def register(self):
        try:
            if not (self.student_ID and self.password):
                raise ValueError
        except ValueError:
            self.printExit('未输入账号密码', 1)

        try:
            self.driver.get(self.url)
            # account -> password -> login
            self.driver.find_element(
                By.XPATH, '/html/body/div[1]/div[2]/div[1]/input').send_keys(self.student_ID)
            self.driver.find_element(
                By.XPATH, '/html/body/div[1]/div[2]/div[2]/input').send_keys(self.password)
            self.driver.find_element(
                By.XPATH, '/html/body/div[1]/div[3]').click()

            # Daily report
            WebDriverWait(driver=self.driver, timeout=self.timeout,
                          poll_frequency=0.5).until(lambda driver: driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div/section/div/div[3]/div/ul/li/span'))
            self.driver.find_element(
                By.XPATH, '/html/body/div[1]/div[1]/div/section/div/div[3]/div/ul/li/span').click()

            # Wait for showing info page
            WebDriverWait(driver=self.driver, timeout=self.timeout,
                          poll_frequency=0.2).until(lambda driver: driver.find_element(By.XPATH, '/html/body/div[1]/div/div/section/div[4]/ul/li[9]/div'))

            # Information
            self.driver.find_element(
                By.XPATH, '/html/body/div[1]/div/div/section/div[4]/ul/li[4]/div/div/div[3]').click()
            self.driver.find_element(
                By.XPATH, '/html/body/div[1]/div/div/section/div[4]/ul/li[5]/div/div/div[2]').click()
            self.driver.find_element(
                By.XPATH, '/html/body/div[1]/div/div/section/div[4]/ul/li[6]/div/div[1]/div[2]').click()
            self.driver.find_element(
                By.XPATH, '/html/body/div[1]/div/div/section/div[4]/ul/li[10]/div/div/div[2]').click()
            self.driver.find_element(
                By.XPATH, '/html/body/div[1]/div/div/section/div[4]/ul/li[11]/div/div/div[2]').click()
            self.driver.find_element(
                By.XPATH, '/html/body/div[1]/div/div/section/div[4]/ul/li[12]/div/div/div[2]').click()

            # Location
            self.driver.find_element(
                By.XPATH, '/html/body/div[1]/div/div/section/div[4]/ul/li[9]/div').click()

            # until page-loading-container.style = 'display: none;'
            WebDriverWait(driver=self.driver, timeout=self.timeout,
                          poll_frequency=0.2).until(lambda driver: driver.find_element(
                              By.XPATH, '/html/body/div[3]').get_attribute('style') == "display: none;")

            # # Submit
            self.driver.find_element(
                By.XPATH, '/html/body/div[1]/div/div/section/div[5]/div/a').click()
        except:
            if os.system('ping www.baidu.com'):
                self.printExit('填报失败：网络未连接', 1)
            else:
                self.printExit(
                    '填报失败：尝试提交前失败，可能是由于位置无法获取', 1)
        try:
            WebDriverWait(driver=self.driver, timeout=self.timeout//10,
                          poll_frequency=0.2).until(lambda driver: driver.find_element(
                              By.XPATH, '/html/body/div[4]/div/div[2]/div[2]'))
            self.driver.find_element(
                By.XPATH, '/html/body/div[4]/div/div[2]/div[2]').click()
        except:
            try:
                info = self.driver.find_element(
                    By.XPATH, '//*[@id="wapat"]/div/div[1]').text
            except:
                self.printExit('填报失败：提交后失败', 1)
            else:
                if info.find('你已提交过') != -1:
                    self.printExit('今日已填报', 0)
                else:
                    self.printExit(f'填报失败：提交后失败，{info}', 1)
        else:
            self.printExit('填报成功', 0)

    def __call__(self):
        self.register()


if __name__ == '__main__':
    with open('./settings.json', 'r', encoding='utf8') as fp:
        settings = json.load(fp)

    time.sleep(settings['delay_time'])
    if settings['alert']:
        toaster = ToastNotifier()
        toaster.show_toast("Registrant",
                           '启动',
                           duration=settings['alert_time'])
    reg = Registrant(url=settings['url'],
                     silent=settings['silent'], alert=settings['alert'], alert_time=settings['alert_time'], timeout=settings['timeout'], student_ID=settings['student_ID'], password=settings['password'])
    reg()
