import flet as ft
import os
import json
import urllib.request
from dotenv import load_dotenv
from openai import OpenAI

# 🚨 환경변수 로드 및 OpenAI 클라이언트 초기화
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def main(page: ft.Page):
    page.title = "MBTI & 연애 궁합 분석기"
    page.theme_mode = ft.ThemeMode.LIGHT

    # ==========================================
    # 4. 대화 분석 결과창 (DALL-E 3 이미지 + GPT JSON 분석)
    # ==========================================
    def show_analysis_screen(file_path, user_name, gender, relationship):
        page.controls.clear()
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.scroll = ft.ScrollMode.AUTO
        
        # 1️⃣ 로딩 화면
        loading_ring = ft.ProgressRing(width=50, height=50, stroke_width=5)
        loading_text = ft.Text("🔍 AI가 카톡 대화를 열심히 분석 중입니다...\n(약 10~20초 소요 ⏳)", text_align="center", size=18, weight="bold")
        page.add(ft.Column([loading_ring, loading_text], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER))
        page.update()

        # 2️⃣ GPT 텍스트 분석 (JSON)
        def get_ai_analysis():
            with open(file_path, 'r', encoding='utf-8') as f:
                chat_content = f.read()

            system_prompt = """
            너는 카카오톡 대화를 분석하여 두 사람의 관계와 성향을 파악하는 전문 심리 분석가야.
            반드시 아래 JSON 형식으로만 답변을 반환해. 다른 말은 절대 덧붙이지 마.
            {
                "user": {
                    "mbti": "ENFP 등 4자리", "e": 80, "n": 60, "f": 90, "p": 70,
                    "likability": 95,
                    "nickname": "대화를 기반으로 한 재미있는 별명 (예: 긍정왕 에너자이저)",
                    "expressions": ["가장 많이 쓴 단어1", "단어2", "단어3"]
                },
                "partner": {
                    "mbti": "INTJ 등 4자리", "e": 30, "n": 80, "f": 40, "p": 20,
                    "likability": 88,
                    "nickname": "상대방의 특징을 잡은 별명 (예: 다정한 팩트폭격기)",
                    "expressions": ["자주 쓴 단어1", "단어2", "단어3"]
                },
                "total_score": 90,
                "summary": "두 사람의 궁합에 대한 1~2줄의 핵심 요약 평가"
            }
            """
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    response_format={ "type": "json_object" },
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"사용자 이름: {user_name}\n상대방 관계: {relationship}\n\n[대화 내용]\n{chat_content}"}
                    ]
                )
                return json.loads(response.choices[0].message.content)
            except Exception as e:
                print(f"API 에러: {e}")
                return None

        # 3️⃣ DALL-E 3 이미지 생성 및 저장 (에셋 폴더 기준 파일명 반환)
        def generate_and_save_image(mbti, nickname, file_name):
            prompt = f"A cute, simple, and lovely 3D cartoon style character representing '{mbti}' personality. The character's vibe perfectly matches the nickname '{nickname}'. Clean solid pastel color background. Highly detailed, trendy 3D icon style."
            try:
                response = client.images.generate(model="dall-e-3", prompt=prompt, size="1024x1024", quality="standard", n=1)
                image_url = response.data[0].url
                
                # 파일 저장은 절대 경로에 확실하게!
                current_dir = os.path.dirname(os.path.abspath(__file__))
                save_path = os.path.join(current_dir, file_name)
                urllib.request.urlretrieve(image_url, save_path)
                
                # Flet 에셋 폴더 기준이므로 파일명만 반환
                return file_name 
            except Exception as e:
                print(f"이미지 생성 에러: {e}")
                return "https://picsum.photos/id/237/300/300" # 에러 시 임시 이미지

        # --- [실제 실행 흐름] ---
        ai_data = get_ai_analysis()
        if not ai_data:
            page.controls.clear()
            page.add(ft.Text("❌ 분석 중 에러가 발생했습니다.", color="red"), ft.ElevatedButton("돌아가기", on_click=lambda _: show_selection_screen(file_path, user_name, gender, relationship)))
            page.update()
            return

        loading_text.value = f"✅ 대화 분석 완료!\n🎨 [{user_name}]님의 캐릭터를 그리는 중입니다...\n(약 10초 소요 ⏳)"
        page.update()
        user_img_path = generate_and_save_image(ai_data["user"]["mbti"], ai_data["user"]["nickname"], "user_character.png")

        loading_text.value = f"✅ [{user_name}]님 캐릭터 완성!\n🎨 상대방의 캐릭터를 그리는 중입니다...\n(약 10초 소요 ⏳)"
        page.update()
        partner_img_path = generate_and_save_image(ai_data["partner"]["mbti"], ai_data["partner"]["nickname"], "partner_character.png")

        # 4️⃣ 화면 그리기
        page.controls.clear()
        page.vertical_alignment = ft.MainAxisAlignment.START

        def make_mbti_bar(left_label, right_label, left_percent):
            return ft.Column([
                ft.Row([ft.Text(left_label, weight="bold", color=ft.Colors.BLUE_700), ft.Text(f"{left_percent}%", color=ft.Colors.BLUE_700), ft.Text("vs", color=ft.Colors.GREY_500), ft.Text(f"{100-left_percent}%", color=ft.Colors.RED_700), ft.Text(right_label, weight="bold", color=ft.Colors.RED_700)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.ProgressBar(value=left_percent/100, color=ft.Colors.BLUE_400, bgcolor=ft.Colors.RED_400, height=12)
            ], spacing=2)

        def build_person_result(name, role, data, img_filename):
            return ft.Container(
                width=420, padding=20, border=ft.border.all(2, ft.Colors.GREY_300), border_radius=15, bgcolor=ft.Colors.WHITE,
                content=ft.Column(
                    [
                        ft.Text(f"{name} ({role})", size=24, weight="bold", color=ft.Colors.BLACK87),
                        ft.Text(f"\"{data['nickname']}\"", size=20, color=ft.Colors.ORANGE_600, weight="bold", italic=True),
                        
                        # 💡 파일명만 쏙! 에셋 폴더 설정 덕분에 브라우저가 알아서 그림을 띄웁니다.
                        ft.Image(src=img_filename, width=300, height=300, fit="cover", border_radius=20),
                        
                        ft.Text(f"추정 MBTI: {data['mbti']}", size=30, color=ft.Colors.PURPLE_600, weight="bold"),
                        
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Text(f"#{exp}", color=ft.Colors.WHITE, size=13, weight="bold"),
                                    bgcolor=ft.Colors.BLUE_GREY_400, padding=ft.Padding(left=10, right=10, top=5, bottom=5), border_radius=20
                                ) for exp in data['expressions']
                            ], 
                            alignment=ft.MainAxisAlignment.CENTER, wrap=True
                        ),
                        
                        ft.Divider(height=20, color="transparent"),
                        ft.Text("상세 성향 지수", size=18, weight="bold"),
                        make_mbti_bar("E", "I", data['e']), make_mbti_bar("N", "S", data['n']), make_mbti_bar("F", "T", data['f']), make_mbti_bar("P", "J", data['p']),
                        ft.Divider(height=20, color="transparent"),
                        ft.Text("💕 상대방을 향한 호감도", size=18, weight="bold", color=ft.Colors.PINK_500),
                        ft.Row([
                            ft.ProgressBar(value=data['likability']/100, color=ft.Colors.PINK_400, bgcolor=ft.Colors.GREY_200, height=20, expand=True),
                            ft.Text(f"{data['likability']}점", size=20, weight="bold")
                        ]),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10
                )
            )

        user_card = build_person_result(user_name, "나", ai_data["user"], user_img_path)
        partner_card = build_person_result("상대방", relationship, ai_data["partner"], partner_img_path)

        summary_panel = ft.Container(
            padding=20, bgcolor=ft.Colors.PINK_50, border_radius=15,
            content=ft.Column([
                ft.Text("💑 두 사람의 종합 궁합 점수", size=22, weight="bold", color=ft.Colors.PINK_700),
                ft.Text(f"{ai_data['total_score']}점!", size=40, weight="bold", color=ft.Colors.RED_500),
                ft.Text(ai_data['summary'], size=16, color=ft.Colors.BLACK87, text_align="center")
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

        page.add(
            ft.Container(height=20),
            ft.Text("📊 대화 분석 결과", size=35, weight="bold"),
            ft.Container(height=10),
            summary_panel,
            ft.Container(height=20),
            ft.Row([user_card, partner_card], alignment=ft.MainAxisAlignment.CENTER, wrap=True),
            ft.Container(height=30),
            ft.ElevatedButton("🔙 선택 화면으로 돌아가기", width=300, height=50, on_click=lambda _: show_selection_screen(file_path, user_name, gender, relationship)),
            ft.Container(height=50)
        )
        page.update()


    # ==========================================
    # 3. 상담 채팅방 화면
    # ==========================================
    def show_chat_room(file_path, user_name, gender, relationship):
        page.controls.clear()
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.horizontal_alignment = ft.CrossAxisAlignment.START
        
        chat_log = ft.ListView(expand=True, spacing=15, auto_scroll=True)
        user_input = ft.TextField(hint_text="메시지를 입력하세요...", expand=True, border_radius=20)
        
        conversation_history = [{"role": "system", "content": "You are a professional MBTI analyzer and relationship counselor."}]

        # 상단에 뒤로 가기 버튼 (ElevatedButton으로 에러 방지)
        back_button = ft.ElevatedButton(
            "🔙 뒤로 가기", 
            on_click=lambda _: show_selection_screen(file_path, user_name, gender, relationship)
        )
        header = ft.Row([back_button, ft.Text("상담 챗봇", size=20, weight="bold")])

        def show_message(text: str, is_user: bool):
            avatar_color = ft.Colors.BLUE_700 if is_user else ft.Colors.GREEN_700
            avatar_text = user_name[0] if is_user else "AI"
            border_radius = ft.border_radius.only(top_left=15, top_right=15, bottom_left=0 if not is_user else 15, bottom_right=0 if is_user else 15)
            bubble_width = 600 if len(text) > 40 else None
            
            msg_bubble = ft.Container(
                content=ft.Text(text, color=ft.Colors.WHITE if is_user else ft.Colors.BLACK87, selectable=True, size=15),
                bgcolor=ft.Colors.BLUE_500 if is_user else ft.Colors.GREY_200,
                border_radius=border_radius, padding=12, width=bubble_width,
            )
            avatar = ft.CircleAvatar(content=ft.Text(avatar_text, color=ft.Colors.WHITE, weight="bold"), bgcolor=avatar_color, radius=18)
            
            row = ft.Row([msg_bubble, avatar], alignment=ft.MainAxisAlignment.END, vertical_alignment=ft.CrossAxisAlignment.START) if is_user else ft.Row([avatar, msg_bubble], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START)
            chat_log.controls.append(row)
            page.update()

        def analyze_chat_file():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    chat_content = f.read()

                prompt = f"다음은 {user_name}({gender})와 상대방('{relationship}')의 카카오톡 대화 원본이야. 링크나 시스템 메시지 등도 모두 포함되어 있어. 이 대화의 문맥과 패턴을 분석해서 두 사람의 MBTI를 유추하고, 궁합과 관계에 대한 조언을 해줘.\n\n[카카오톡 데이터]\n{chat_content}"

                show_message(f"데이터를 읽어왔습니다.\nAI가 대화를 꼼꼼히 분석 중입니다. 잠시만 기다려주세요... ⏳", False)
                user_input.disabled = True
                page.update()

                conversation_history.append({"role": "user", "content": prompt})
                response = client.chat.completions.create(model="gpt-4o", messages=conversation_history)
                
                bot_message = response.choices[0].message.content.strip()
                show_message(bot_message, False)
                conversation_history.append({"role": "assistant", "content": bot_message})

            except Exception as e:
                show_message(f"❌ 파일 분석 중 오류가 발생했습니다: {e}", False)
            finally:
                user_input.disabled = False
                user_input.focus()
                page.update()

        def send_click(e):
            user_text = user_input.value.strip()
            if not user_text: return

            show_message(user_text, True)
            conversation_history.append({"role": "user", "content": user_text})
            user_input.value = ""
            user_input.disabled = True
            page.update()

            try:
                response = client.chat.completions.create(model="gpt-4o", messages=conversation_history)
                bot_message = response.choices[0].message.content.strip()
                show_message(bot_message, False)
                conversation_history.append({"role": "assistant", "content": bot_message})
            except Exception as ex:
                show_message(f"오류 발생: {ex}", False)

            user_input.disabled = False
            user_input.focus()
            page.update()

        send_button = ft.ElevatedButton("전송", on_click=send_click)
        user_input.on_submit = send_click

        page.add(header, chat_log, ft.Row([user_input, send_button]))
        analyze_chat_file()


    # ==========================================
    # 2. 중간 선택 화면 (라우팅)
    # ==========================================
    def show_selection_screen(file_path, user_name, gender, relationship):
        page.controls.clear()
        page.update()
        
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        content_column = ft.Column(
            [
                ft.Text("✅", size=60), 
                ft.Text("데이터 업로드 완료!", size=30, weight="bold"),
                ft.Text("어떤 화면으로 이동하시겠어요?", size=18, color=ft.Colors.GREY_700),
                ft.Container(height=30),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "📊 대화 분석 결과 보기", 
                            width=250, height=60, 
                            on_click=lambda _: show_analysis_screen(file_path, user_name, gender, relationship)
                        ),
                        ft.ElevatedButton(
                            "💬 상담 채팅방 입장", 
                            width=250, height=60, 
                            on_click=lambda _: show_chat_room(file_path, user_name, gender, relationship)
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        page.add(content_column)
        page.update()


    # ==========================================
    # 1. 유저 정보 입력 화면
    # ==========================================
    def show_input_screen():
        page.controls.clear()
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        def submit_user_info(e):
            target_file = file_input.value.strip()
            name = name_field.value.strip()
            gender = gender_dropdown.value
            relationship = relationship_dropdown.value
            
            if not target_file:
                file_input.error_text = "파일명을 입력해주세요!"
                page.update()
                return
                
            current_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(current_dir, target_file)
            
            if not os.path.exists(file_path):
                file_input.error_text = f"파일을 찾을 수 없습니다!"
                page.update()
                return

            show_selection_screen(file_path, name, gender, relationship)

        file_input = ft.TextField(label="카카오톡 텍스트 파일명 (예: test.txt)", width=400)
        name_field = ft.TextField(label="Your Name", width=400)
        gender_dropdown = ft.Dropdown(label="Gender", width=400, options=[ft.dropdown.Option("Male"), ft.dropdown.Option("Female")], value="Male")
        relationship_dropdown = ft.Dropdown(label="Relationship", width=400, options=[ft.dropdown.Option("Couple"), ft.dropdown.Option("Friend")], value="Couple")
        submit_button = ft.ElevatedButton("Submit & Next", on_click=submit_user_info, width=400)

        page.add(
            ft.Column(
                [
                    ft.Text("Step 1. 정보 입력", size=24, weight="bold"),
                    file_input, name_field, gender_dropdown, relationship_dropdown, submit_button
                ], 
                alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER 
            )
        )
        page.update()

    # 앱 시작점
    show_input_screen()

# 💡 웹 브라우저 뷰 모드 및 에셋 폴더 권한 부여 (로컬 이미지 띄우기)
current_dir = os.path.dirname(os.path.abspath(__file__))
ft.app(main, view=ft.AppView.WEB_BROWSER, assets_dir=current_dir)