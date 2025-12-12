import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageTk
import pygame
import random
import torch
from transformers import CLIPProcessor, CLIPModel

# ====== 기본 설정 ======
CANVAS_WIDTH = 900
CANVAS_HEIGHT = 600

# ====== 전체 제시어 ======
ALL_PROMPTS = [
    "사과", "고양이", "사다리", "나무", "자동차", "부엉이", "의자", "전기톱", "폭탄", "딸기", "검", "황소", "도마뱀",
    "물고기", "강아지", "꽃", "비행기", "컵", "칫솔", "바나나", "알약", "우주왕복선", "고기", "장갑", "화염방사기", "용",
    "스마트폰", "텔레비전", "조개", "문어", "연필", "건전지", "쇠사슬", "빵", "교회", "거미", "무량공처", "벽돌", "탄산음료",
    "전구", "독수리", "활", "헬리콥터", "배", "캥거루", "운동화", "책"
]

PROMPT_MAP = {
    "사과": "apple", "바나나": "banana", "고양이": "cat", "딸기": "strawberry", "폭탄": "boom", "장갑": "glove",
    "사다리": "ladder", "나무": "tree", "자동차": "car", "의자": "chair", "고기": "meat", "총": "gun", "검": "sword",
    "부엉이": "owl", "전기톱": "chainsaw", "물고기": "fish", "강아지": "puppy", "꽃": "flower", "조개": "clam",
    "비행기": "airplane", "컵": "cup", "칫솔": "toothbrush", "알약": "pill", "우주왕복선": "Space Shuttle", "황소": "bull",
    "화염방사기": "flamethrower", "도마뱀": "lizard", "용(드래곤)": "dragon", "스마트폰": "smartphone", "텔레비전": "TV",
    "문어": "octopus", "연필": "pencil", "건전지": "battery", "쇠사슬": "chain", "빵": "bread", "교회": "church",
    "거미": "spider", "[무량공처]": "Satoru Gojo", "벽돌": "brick", "탄산음료": "soda", "전구": "light", "독수리": "eagle",
    "활": "arrow", "헬리콥터": "helicopter", "배(선박)": "ship", "캥거루": "kangaroo", "운동화": "sneakers", "책": "book"
}


class PaintGame:
    def __init__(self, root):
        self.root = root
        self.root.title("AI 드로잉 교육 게임")
        self.root.resizable(False, False)

        # 게임 상태 변수
        self.success_count = 0  # 성공 갯수 카운트

        # ============================================
        # AI 모델 로딩
        # ============================================
        print("AI 모델을 로딩 중입니다... 잠시만 기다려주세요.")
        try:
            self.model_name = "openai/clip-vit-base-patch32"
            self.model = CLIPModel.from_pretrained(self.model_name)
            self.processor = CLIPProcessor.from_pretrained(self.model_name)
            print("AI 모델 로딩 완료!")
        except Exception as e:
            print(f"AI 모델 로딩 실패: {e}")
            self.model = None

        # ============================================
        # 음악 재생
        # ============================================
        pygame.mixer.init()
        try:
            pygame.mixer.music.load("animalforest.mp3")
            pygame.mixer.music.play(-1)
        except:
            pass

        # ============================================
        # 1. 표지 화면 (Lobby)
        # ============================================
        self.cover_frame = tk.Frame(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
        self.cover_frame.pack()
        self.cover_frame.pack_propagate(False)

        try:
            cover_img = Image.open("mainlobby.jpg")
            cover_img = cover_img.resize((CANVAS_WIDTH, CANVAS_HEIGHT))
            self.cover_photo = ImageTk.PhotoImage(cover_img)
        except:
            self.cover_photo = None

        if self.cover_photo:
            self.cover_label = tk.Label(self.cover_frame, image=self.cover_photo)
        else:
            self.cover_label = tk.Label(self.cover_frame, text="AI 드로잉 게임", bg="lightblue", font=("Arial", 30))
        self.cover_label.pack(fill="both", expand=True)

        # [시작 버튼]
        self.cover_button = tk.Button(self.cover_frame, text="게임 시작", font=("Arial", 18, "bold"),
                                      bg="white", fg="black", command=self.start_game)
        self.cover_button.place(relx=0.5, rely=0.75, anchor="center")

        # [튜토리얼 버튼]
        self.tutorial_btn = tk.Button(self.cover_frame, text="도움말", font=("Arial", 12),
                                      command=self.show_tutorial)
        self.tutorial_btn.place(relx=0.5, rely=0.88, anchor="center")

        # ============================================
        # 2. 튜토리얼 오버레이 (다중 페이지 지원)
        # ============================================
        self.tutorial_frame = tk.Frame(self.cover_frame, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="black")

        # 튜토리얼 이미지 2장 로드
        self.tutorial_images = []
        image_files = ["ttt1.jpg", "ttt2.jpg"]

        for f in image_files:
            try:
                img = Image.open(f).resize((CANVAS_WIDTH, CANVAS_HEIGHT))
                self.tutorial_images.append(ImageTk.PhotoImage(img))
            except:
                print(f"{f}를 찾을 수 없습니다.")

        if not self.tutorial_images:
            temp_img = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "gray")
            self.tutorial_images.append(ImageTk.PhotoImage(temp_img))

        self.current_tut_page = 0

        # 이미지를 보여줄 라벨
        self.tut_label = tk.Label(self.tutorial_frame, image=self.tutorial_images[0], bg="black")
        self.tut_label.pack(fill="both", expand=True)

        # [X 닫기 버튼]
        self.close_btn = tk.Button(self.tutorial_frame, text="X", font=("Arial", 15, "bold"),
                                   bg="red", fg="white", command=self.hide_tutorial)
        self.close_btn.place(relx=0.95, rely=0.08, anchor="center")

        # [이전 버튼]
        self.prev_btn = tk.Button(self.tutorial_frame, text="◀ 이전", font=("Arial", 12, "bold"),
                                  command=self.prev_tutorial_page)
        self.prev_btn.place_forget()

        # [다음 버튼]
        self.next_btn = tk.Button(self.tutorial_frame, text="다음 ▶", font=("Arial", 12, "bold"),
                                  command=self.next_tutorial_page)
        self.next_btn.place_forget()

        # ============================================
        # 3. 게임 화면
        # ============================================
        self.game_frame = tk.Frame(root)

        # 시작 시 랜덤 제시어 7개 선택
        self.prompts = random.sample(ALL_PROMPTS, 7)
        self.current_prompt_index = 0

        self.prompt_label = tk.Label(self.game_frame, font=("Arial", 18))

        try:
            bg_img = Image.open("maingame.jpg")
            bg_img = bg_img.resize((CANVAS_WIDTH, CANVAS_HEIGHT))
            self.bg_photo = ImageTk.PhotoImage(bg_img)
        except:
            self.bg_photo = None

        self.canvas = tk.Canvas(self.game_frame, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white")
        if self.bg_photo:
            self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        self.image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "white")
        self.draw = ImageDraw.Draw(self.image)

        self.last_x, self.last_y = None, None
        self.canvas.bind("<ButtonPress-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw_line)

        self.check_button = tk.Button(self.game_frame, text="만디에게 보여주기", font=("Arial", 14),
                                      command=self.check_answer)

    # ====== 튜토리얼 관련 함수 ======
    def show_tutorial(self):
        self.current_tut_page = 0
        self.update_tutorial_ui()
        self.tutorial_frame.place(x=0, y=0)

    def hide_tutorial(self):
        self.tutorial_frame.place_forget()

    def next_tutorial_page(self):
        if self.current_tut_page < len(self.tutorial_images) - 1:
            self.current_tut_page += 1
            self.update_tutorial_ui()

    def prev_tutorial_page(self):
        if self.current_tut_page > 0:
            self.current_tut_page -= 1
            self.update_tutorial_ui()

    def update_tutorial_ui(self):
        self.tut_label.config(image=self.tutorial_images[self.current_tut_page])

        if self.current_tut_page == 0:
            self.prev_btn.place_forget()
        else:
            self.prev_btn.place(relx=0.9, rely=0.9, anchor="center")

        if self.current_tut_page == len(self.tutorial_images) - 1:
            self.next_btn.place_forget()
        else:
            self.next_btn.place(relx=0.9, rely=0.9, anchor="center")

    # ====== 게임 재시작 함수 ======
    def restart_game(self):
        self.game_frame.pack_forget()
        self.cover_frame.pack()

        self.prompts = random.sample(ALL_PROMPTS, 10)
        self.current_prompt_index = 0
        self.success_count = 0

        self.reset_canvas()

    # ====== 게임 진행 함수 ======
    def start_game(self):
        self.cover_frame.pack_forget()
        self.success_count = 0

        self.prompt_label.config(text=f"필요한 준비물: {self.prompts[self.current_prompt_index]}")
        self.prompt_label.pack(pady=10)
        self.canvas.pack(pady=5)
        self.check_button.pack(pady=10)
        self.game_frame.pack()

    def start_draw(self, event):
        self.last_x, self.last_y = event.x, event.y

    def draw_line(self, event):
        self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, fill="black", width=5, capstyle=tk.ROUND,
                                smooth=True)
        self.draw.line((self.last_x, self.last_y, event.x, event.y), fill="black", width=5)
        self.last_x, self.last_y = event.x, event.y

    def reset_canvas(self):
        self.canvas.delete("all")
        if self.bg_photo:
            self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")
        self.image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "white")
        self.draw = ImageDraw.Draw(self.image)

    # ====== AI 점수 계산 (글씨 감지 강화) ======
    def calculate_ai_score(self, target_word_kr):
        if self.model is None:
            return random.randint(30, 70)

        target_word_en = PROMPT_MAP.get(target_word_kr, "object")

        # [0] 그림, [1] 정답 단어 글씨(함정), [2-3] 일반 글씨, [4-5] 무의미
        text_prompts = [
            f"a sketch of a {target_word_en}",
            f"the written word '{target_word_en}'",
            "written text",
            "handwriting and letters",
            "messy scribbles",
            "blank white paper"
        ]

        inputs = self.processor(text=text_prompts, images=self.image, return_tensors="pt", padding=True)
        with torch.no_grad():
            outputs = self.model(**inputs)

        probs = outputs.logits_per_image.softmax(dim=1)[0]

        prob_drawing = probs[0].item()
        prob_word_text = probs[1].item()
        prob_general_text = probs[2].item() + probs[3].item()

        total_text_prob = prob_word_text + prob_general_text

        print(f"[{target_word_kr}] ")
        print("글씨:", total_text_prob)
        print("그림:", prob_drawing)

        final_score = int(prob_drawing * 100)

        # 글씨 감지 시 페널티 적용
        if total_text_prob > prob_drawing or total_text_prob > 0.25:
            print(">> 글씨 감지됨! 점수 대폭 삭감")
            final_score = min(20, int(final_score * 0.2))

        if final_score < 10: final_score = 10
        if final_score > 98: final_score = 100

        return final_score, total_text_prob

    # ====== 정답 확인 및 결과 처리 (카운트 기능 추가) ======
    def check_answer(self):
        self.check_button.config(text="채점 중...", state="disabled")
        self.root.update()

        answer_kr = self.prompts[self.current_prompt_index]
        score, text = self.calculate_ai_score(answer_kr)

        self.check_button.config(text="만디에게 보여주기", state="normal")

        # 50점 넘으면 성공 카운트 증가
        if score > 50:
            self.success_count += 1

        msg = f"점수: {score}점"
        if score > 85:
            msg += "\n우와! 정말 잘 그렸다요. 완벽하게 알아봤다요."
        elif score > 50:
            msg += "\n특징을 잘 잡은거다요! 대충 알겠다요!"
        else:
            msg += "\n미안하다요... 잘 모르겠다요..."

        if text > 0.25:
            msg += "? \n 우씨, 만디는 글씨를 못읽는 거다요!"

        messagebox.showinfo("만디의 생각", f"필요한 준비물: {answer_kr}\n{msg}")

        self.current_prompt_index += 1

        # 마지막 문제까지 다 풀었을 때
        if self.current_prompt_index >= len(self.prompts):
            total_items = len(self.prompts)

            # 최종 결과 메시지 구성
            result_msg = f"총 {total_items}개의 준비물 중 {self.success_count}개를 챙겼다요!\n"
            if self.success_count == total_items:
                result_msg += "완벽하다요!"
            elif self.success_count >= 4:
                result_msg += "이 정도면 충분하다요! 출발하자요!"
            else:
                result_msg += "으음... 뭔가 많이 빠트린 것 같다요..."

            play_again = messagebox.askyesno(
                "게임 종료!",
                f"{result_msg}\n\n게임을 다시 시작하겠다요?"
            )

            if play_again:
                self.restart_game()
            else:
                self.root.destroy()
            return

        self.prompt_label.config(text=f"필요한 준비물: {self.prompts[self.current_prompt_index]}")
        self.reset_canvas()


if __name__ == "__main__":
    root = tk.Tk()
    app = PaintGame(root)
    root.mainloop()