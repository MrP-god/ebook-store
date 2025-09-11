import os 
import requests
from dotenv import load_dotenv

load_dotenv()


def send_verification_email(code, mail):
    response=requests.post(
        "https://api.mailgun.net/v3/sandbox67645b12702a402099aa4e39a4ef21b9.mailgun.org/messages",
        auth=("api", os.getenv("MAILGUN_KEY")),
        data={
            "from": "ivanov Mailbook <postmaster@sandbox67645b12702a402099aa4e39a4ef21b9.mailgun.org>",
            "to": f"Artiom Ivanv <{mail}>",
            "subject": "ivanov ebook store ",
            "text": f"test verification email, ur code is : {code},\n \n this is an automatic response :), leave this folk alone. \n have a nice day"
        }    
    )   

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    return response





