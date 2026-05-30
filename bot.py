import discord
from discord import app_commands
import random
import json
import os
from datetime import datetime

# ================== 설정 ==================
# ⚠️ 주의: 여기에 새로 재발급받으신 토큰을 넣으세요!
TOKEN = "0
ALLOWED_ROLE_ID = 1510323534017335319

DATA_FILE = "codes.json"
LOG_FILE = "logs.json"

# 인텐트 설정 (개발자 포털에서 Server Members Intent가 켜져 있어야 작동합니다!)
intents = discord.Intents.default()
intents.members = True  

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# ================== 데이터 로드/저장 ==================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_logs(logs):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)

# ================== 9자리 코드 생성 ==================
def generate_code():
    return ''.join(random.choices('0123456789', k=9))

# ================== 명령어 ==================
@tree.command(name="비밀코드발급", description="9자리 비밀 코드를 발급받습니다. (한 번만 발급)")
async def issue_code(interaction: discord.Interaction):
    # 🌟 [추가] 지정된 역할을 가지고 있는지 확인
    user_roles = [role.id for role in interaction.user.roles]
    if ALLOWED_ROLE_ID not in user_roles:
        await interaction.response.send_message(
            f"❌ 이 명령어는 지정된 역할(<@&{ALLOWED_ROLE_ID}>)을 가진 사람만 사용할 수 있습니다.",
            ephemeral=True
        )
        return

    user_id = str(interaction.user.id)
    data = load_data()

    if user_id in data:
        await interaction.response.send_message(
            f"⚠️ 이미 발급받은 코드가 있습니다.\n`{data[user_id]}`\n\n`/조회` 명령어로 확인하세요.", 
            ephemeral=True
        )
        return

    code = generate_code()
    data[user_id] = code
    save_data(data)

    # 로그 저장
    logs = load_logs()
    logs.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user_id,
        "username": str(interaction.user),
        "code": code
    })
    save_logs(logs)

    await interaction.response.send_message(
        f"✅ **비밀 코드가 발급되었습니다!**\n\n`{code}`\n\n**절대 타인에게 공유하지 마세요!**",
        ephemeral=True
    )

@tree.command(name="조회", description="내가 발급받은 비밀 코드를 확인합니다.")
async def check_code(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    data = load_data()

    if user_id in data:
        await interaction.response.send_message(
            f"🔍 **당신의 비밀 코드**\n\n`{data[user_id]}`", 
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "❌ 아직 발급받은 코드가 없습니다.\n`/비밀코드발급` 명령어를 사용해주세요.", 
            ephemeral=True
        )

# 🌟 [수정된 부분] 오직 관리자 권한(Administrator)이 있는 사람에게만 명령어가 보이고 작동합니다.
@tree.command(name="로그", description="관리자 전용 - 코드 발급 로그 확인")
@app_commands.default_permissions(administrator=True)  
async def view_logs(interaction: discord.Interaction):
    logs = load_logs()
    
    if not logs:
        await interaction.response.send_message("📋 아직 발급된 로그가 없습니다.", ephemeral=True)
        return

    # 최근 10개만 추출해서 보여주기
    recent_logs = logs[-10:]
    msg = "**📋 비밀코드 발급 로그 (최근 10건)**\n\n"
    
    for log in reversed(recent_logs):
        msg += f"**{log['timestamp']}**\n"
        msg += f"👤 {log['username']} (`{log['user_id']}`)\n"
        msg += f"🔑 `{log['code']}`\n\n"

    await interaction.response.send_message(msg, ephemeral=True)

# 🌟 [추가 기능] 관리자가 특정 유저의 코드를 개별 조회할 수 있는 명령어입니다.
@tree.command(name="유저코드조회", description="관리자 전용 - 특정 유저가 발급받은 코드를 조회합니다.")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(유저="조회할 대상 유저를 선택하세요.")
async def view_user_code(interaction: discord.Interaction, 유저: discord.Member):
    target_id = str(유저.id)
    data = load_data()
    
    if target_id in data:
        await interaction.response.send_message(
            f"📋 **{유저.display_name}**님의 코드: `{data[target_id]}`",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"❌ **{유저.display_name}**님은 아직 코드를 발급받지 않았습니다.",
            ephemeral=True
        )

# 🌟 [추가 기능] 모든 유저의 발급 데이터를 초기화하는 명령어입니다.
@tree.command(name="데이터초기화", description="관리자 전용 - 발급된 모든 코드 데이터를 완전히 초기화합니다.")
@app_commands.default_permissions(administrator=True)
async def reset_all_data(interaction: discord.Interaction):
    # 빈 딕셔너리를 저장하여 초기화
    save_data({})
    
    # 초기화 내역 로그 기록
    logs = load_logs()
    logs.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": str(interaction.user.id),
        "username": str(interaction.user),
        "code": "전체 데이터 초기화 실행됨"
    })
    save_logs(logs)
    
    await interaction.response.send_message(
        "💥 **[완료]** 모든 코드 발급 데이터가 성공적으로 초기화되었습니다.",
        ephemeral=True
    )

# ================== 봇 시작 ==================
@bot.event
async def on_ready():
    await tree.sync()  # 서버에 슬래시 명령어 동기화
    print(f"✅ {bot.user} 로그인 완료!")
    print("슬래시 명령어가 정상적으로 동기화되었습니다.")

# 맨 위 설정한 TOKEN 변수를 사용하여 봇을 실행합니다.
bot.run(TOKEN)