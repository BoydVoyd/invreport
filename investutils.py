import json
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from base64 import b64encode, b64decode
import mechanize
from bs4 import BeautifulSoup
import re
import urllib
import gspread 
from oauth2client.service_account import ServiceAccountCredentials 
import datetime
import paramiko

class PasswordLoader(object):
    
    def __init__(self, pwfile='.birthdays', private_key_file='/Users/ndavis/.ssh/birthday_rsa' ):
        self.pwfile = pwfile
        self.private_key_file = private_key_file
        self.pw_server = '10.211.55.13'
        self.pw_server_user = 'hiro'
        self.pw_server_key = paramiko.RSAKey.from_private_key_file('/Users/ndavis/.ssh/reason_rsa')
        
        
    def get_passwords(self):
        self.passwords = {}

        with open(self.private_key_file, 'r')as  f:
            self.private_key = RSA.importKey(f.read())
            self.cipher = PKCS1_OAEP.new(self.private_key)
            
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.pw_server, username=self.pw_server_user, pkey=self.pw_server_key)
        self.stdin, self.stdout, self.stderr = self.ssh.exec_command('cat ~/birthday/.birthdays')
        self.file_contents = self.stdout.read()
        self.pw_ciphers = json.loads(self.file_contents)

#        with open(self.pwfile, 'r') as f:
#            self.pw_ciphers = json.loads(f.read())

        for key, value in self.pw_ciphers.iteritems():
            self.passwords[key] = self.cipher.decrypt(b64decode(self.pw_ciphers[key]),)

        return self.passwords

class JHLoader(object):
    
    def __init__(self, password):
        self.LOGIN_PAGE = 'https://www.jhancockpensions.com/do/registration/userSecurityInfo'
        self.CUSTOMER_EMAIL = 'nathanwdavis@gmail.com'
        self.USERNAME = 'nwdavis'
        self.PASSWORD = password
        self.BUTTON_CLICKED = 'Signin'

        self.strip_script = re.compile(r'<script\s+.*?</script>', re.I + re.S)

        # Initialize mechanize settings
        self.br = mechanize.Browser()
        self.br.set_handle_robots(False)
        self.br.set_handle_refresh(True, 10, True)
        self.br.set_handle_redirect(True)
        # This e-mail address will be appended to the User-Agent header, so
        # the site can contact you about your scraping if they so desire.
        self.br.addheaders = [
            ('User-agent',
                'Mozilla/5.0 (X11; U; Linux i686; en-US; rv 1.0) %s' % self.CUSTOMER_EMAIL),
        ]
        
    def get_balance(self):
        self.br.open(self.LOGIN_PAGE)
        self.br.select_form(nr=0)
        self.br.form.set_all_readonly(False)
        self.br['buttonClicked'] = self.BUTTON_CLICKED
        self.br['username'] = self.USERNAME
        self.br['password'] = self.PASSWORD
        self.r = self.br.submit()
        self.soup = BeautifulSoup(self.strip_script.sub('', self.r.get_data()), "lxml")
        self.bal = self.soup.find_all("span", class_="text-5xl")
        self.b = self.bal[0].get_text().strip()[1:]
        return self.b

class PAILoader(object):
    
    def __init__(self, password):
        self.CUSTOMER_EMAIL = 'nathanwdavis@gmail.com'
        self.USERNAME = 'riserobotsrise'
        self.PASSWORD = password
        self.LOGIN_PAGE = 'https://www.pai.com'
        self.START_PAGE = 'https://apps.pai.com/individual/start'
        self.REDIRECT_PAGE = 'https://apps.pai.com/individual/Start/Redirect/'
        self.RETIREMENT_PAGE = 'https://apps.pai.com/individual/retirement'
        
        self.strip_script = re.compile(r'<script\s+.*?</script>', re.I + re.S)
        
        # Initialize mechanize settings
        self.br = mechanize.Browser()
        self.br.set_handle_robots(False)
        self.br.set_handle_refresh(True, 10, True)
        self.br.set_handle_redirect(True)
        # This e-mail address will be appended to the User-Agent header, so
        # the site can contact you about your scraping if they so desire.
        self.br.addheaders = [
            ('User-agent',
                'Mozilla/5.0 (X11; U; Linux i686; en-US; rv 1.0) %s' % self.CUSTOMER_EMAIL),
        ]
        
    def get_balance(self):
        self.br.open(self.LOGIN_PAGE)
        self.br.select_form(nr=2)
        self.br.form.set_all_readonly(False)
        self.br['userName'] = self.USERNAME
        self.br['password'] = self.PASSWORD
        self.r0 = self.br.submit()
        self.parsed_json = json.loads(self.r0.get_data())
        self.redirect_url = self.parsed_json['RedirectUrl']
        self.r1 = self.br.open(self.redirect_url)
        self.soup = BeautifulSoup(self.strip_script.sub('', self.r1.get_data()), "lxml")
        self.hidden_input = self.soup.find_all("input", id ="hfContext")
        self.context = self.hidden_input[0]['value']
        self.parameters = {'_context': self.context}
        self.data = urllib.urlencode(self.parameters)
        self.r2 = self.br.open(self.START_PAGE)
        self.r3 = self.br.open(self.REDIRECT_PAGE, self.data)
        self.r4 = self.br.open(self.RETIREMENT_PAGE)
        self.soup2 = BeautifulSoup(self.strip_script.sub('', self.r4.get_data()), "lxml")
        self.bal = self.soup2.find_all("div", id = "BalanceBarID_BalanceValue")
        self.b = self.bal[0].get_text().strip()[1:]
        return self.b

class SheetLoader(object):
    
    def __init__(self, api_key_file='My Project-2b5ae29ebbed.json', sheet_name='401k'):
        self.api_key_file = api_key_file
        self.sheet_name = sheet_name
        self.SCOPE = ['https://spreadsheets.google.com/feeds']        

        self.FORMAT = '%m/%d/%Y'
        self.today = datetime.datetime.today().strftime(self.FORMAT)

        # use creds to create a client to interact with the Google Drive API
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(self.api_key_file, self.SCOPE)
        self.client = gspread.authorize(self.creds)
        
        # Find a workbook by name and open the first sheet
        self.sheet = self.client.open(self.sheet_name).sheet1

        # Load data from the sheet
        self.sheet_data = self.sheet.get_all_values()
        
        # Get the number of rows in the sheet
        self.next_row = len(self.sheet_data) + 1
        
        #Set the string for the formula to sum the balances
        self.formula_string = '=IF(SUM(B' + str(self.next_row) + ':D' + str(self.next_row) + ')>0,SUM(B' + str(self.next_row) + ':D' + str(self.next_row) +'),"")'
        
    # See if today's balances are already in the sheet
    def check_date(self):
        self.dates = []
        for h in self.sheet_data:
            self.dates.append(h[0])
        self.dates = self.dates[1:]
        if self.today in self.dates:
            return True
        else:
            return False
        
    #Insert today's balances in the sheet
    def insert_balances(self, fid_balance, jh_balance, pai_balance):
        self.fid_balance = fid_balance
        self.jh_balance = jh_balance
        self.pai_balance = pai_balance
        
        self.row = [self.today, self.fid_balance, self.jh_balance, self.pai_balance, self.formula_string]
        self.sheet.insert_row(self.row, self.next_row)

class FidelityLoader(object):
    
    def __init__(self, password):
        self.PIN = password
        self.LOGIN_PAGE = 'https://login.fidelity.com/ftgw/Fas/Fidelity/RtlCust/Login/Init'
        self.REDIRECT_PAGE = 'https://oltx.fidelity.com/ftgw/fbc/ofsummary/defaultPage,_top'
        self.LANDING_PAGE = 'https://workplaceservices.fidelity.com/mybenefits/navstation/navigation'
        self.CUSTOMER_EMAIL = 'nathanwdavis@gmail.com'
        self.DEVICE_PRINT = 'version%3D3.4.2.0_1%26pm_fpua%3Dmozilla%2F5.0+%28macintosh%3B+intel+mac+os+x+10_12_5%29+applewebkit%2F537.36+%28khtml%2C+like+gecko%29+chrome%2F58.0.3029.110+safari%2F537.36%7C5.0+%28Macintosh%3B+Intel+Mac+OS+X+10_12_5%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F58.0.3029.110+Safari%2F537.36%7CMacIntel%26pm_fpsc%3D24%7C2560%7C1440%7C1337%26pm_fpsw%3D%26pm_fptz%3D-6%26pm_fpln%3Dlang%3Den-US%7Csyslang%3D%7Cuserlang%3D%26pm_fpjv%3D0%26pm_fpco%3D1%26pm_fpasw%3Dwidevinecdmadapter%7Cmhjfbmdgcfjbbpaeojofohoefgiehjai%7Cinternal-nacl-plugin%7Cinternal-pdf-viewer%26pm_fpan%3DNetscape%26pm_fpacn%3DMozilla%26pm_fpol%3Dtrue%26pm_fposp%3D%26pm_fpup%3D%26pm_fpsaw%3D2560%26pm_fpspd%3D24%26pm_fpsbd%3D%26pm_fpsdx%3D%26pm_fpsdy%3D%26pm_fpslx%3D%26pm_fpsly%3D%26pm_fpsfse%3D%26pm_fpsui%3D%26pm_os%3DMac%26pm_brmjv%3D58%26pm_br%3DChrome%26pm_inpt%3D%26pm_expt%3D&SSN=nathanwdavis&SavedIdInd=N&PIN=BL6EdT2yI2Ed'
        self.SSN = 'nathanwdavis'
        
        self.strip_script = re.compile(r'<script\s+.*?</script>', re.I + re.S)

        # Initialize mechanize settings
        self.br = mechanize.Browser()
        self.br.set_handle_robots(False)
        self.br.set_handle_refresh(True, 10, True)
        self.br.set_handle_redirect(True)
        # This e-mail address will be appended to the User-Agent header, so
        # the site can contact you about your scraping if they so desire.
        self.br.addheaders = [
            ('User-agent',
                'Mozilla/5.0 (X11; U; Linux i686; en-US; rv 1.0) %s' % self.CUSTOMER_EMAIL),
        ]
        
    def get_balance(self):
        self.br.open(self.LOGIN_PAGE)
        self.br.select_form('Login')
        self.br.form.set_all_readonly(False)
        self.user = self.br.find_control(name="SSN", nr=1)
        self.user.value = self.SSN
        self.br['PIN'] = self.PIN
        self.br['DEVICE_PRINT'] = self.DEVICE_PRINT
        self.br.submit()
        self.br.open(self.REDIRECT_PAGE)
        self.r = self.br.open(self.LANDING_PAGE)
        self.soup = BeautifulSoup(self.strip_script.sub('', self.r.get_data()), "lxml")
        self.bal = self.soup.find_all("div", class_="balance-placeholder")
        self.b = self.bal[1].get_text().strip()[1:]
        return self.b