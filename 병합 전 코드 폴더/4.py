import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageTk
import pygame
import random
import torch
from transformers import CLIPProcessor, CLIPModel

# ====== 기본 설정 ======
CANVAS_WIDTH = 600
CANVAS_HEIGHT = 400

# ====== 전체 제시어 ======
ALL_PROMPTS = [
    "사과", "고양이", "사다리", "나무", "자동차", "부엉이", "의자", "전기톱", "폭탄", "딸기", "검", "황소", "도마뱀",
    "물고기", "강아지", "꽃", "비행기", "컵", "칫솔", "바나나", "알약", "우주왕복선", "고기", "장갑", "화염방사기", "용",
    "스마트폰", "텔레비전", "조개", "문어", "연필", "건전지", "쇠사슬", "빵", "교회", "거미", "무량공처", "벽돌"
]

PROMPT_MAP = {
    "사과": "apple", "바나나": "banana", "고양이": "cat", "딸기": "strawberry", "폭탄": "boom", "장갑": "glove",
    "사다리": "ladder", "나무": "tree", "자동차": "car", "의자": "chair", "고기": "meat", "총": "gun", "검": "sword",
    "부엉이": "owl", "전기톱": "chainsaw", "물고기": "fish", "강아지": "puppy", "꽃": "flower", "조개": "clam",
    "비행기": "airplane", "컵": "cup", "칫솔": "toothbrush", "알약":"pill", "우주왕복선": "Space Shuttle", "황소": "bull",
    "화염방사기": "flamethrower", "도마뱀": "lizard", "용(드래곤)": "dragon", "스마트폰": "smartphone", "텔레비전": "TV",
    "문어": "octopus", "연필": "pencil", "건전지": "battery", "쇠사슬": "chain", "빵": "bread", "교회": "church",
    "거미": "spider", "무량공처": "Unlimited Void", "벽돌": "brick"
}


class PaintGame:
    def __init__(self, root):
        self.root = root
        self.root.title("AI 드로잉 교육 게임")
        self.root.resizable(False, False)

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
        image_files = ["ttt1.jpg", "ttt2.jpg"]  # 파일명 리스트

        for f in image_files:
            try:
                img = Image.open(f).resize((CANVAS_WIDTH, CANVAS_HEIGHT))
                self.tutorial_images.append(ImageTk.PhotoImage(img))
            except:
                print(f"{f}를 찾을 수 없습니다.")

        # 이미지가 하나도 없으면 임시 이미지 생성 (에러 방지)
        if not self.tutorial_images:
            temp_img = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "gray")
            self.tutorial_images.append(ImageTk.PhotoImage(temp_img))

        self.current_tut_page = 0  # 현재 페이지 인덱스

        # 이미지를 보여줄 라벨
        self.tut_label = tk.Label(self.tutorial_frame, image=self.tutorial_images[0], bg="black")
        self.tut_label.pack(fill="both", expand=True)

        # [X 닫기 버튼] (우측 상단)
        self.close_btn = tk.Button(self.tutorial_frame, text="X", font=("Arial", 15, "bold"),
                                   bg="red", fg="white", command=self.hide_tutorial)
        self.close_btn.place(relx=0.95, rely=0.08, anchor="center")

        # [이전 버튼] (좌측 하단)
        self.prev_btn = tk.Button(self.tutorial_frame, text="◀ 이전", font=("Arial", 12, "bold"),
                                  command=self.prev_tutorial_page)
        self.prev_btn.place(relx=0.9, rely=0.9, anchor="center")

        # [다음 버튼] (우측 하단)
        self.next_btn = tk.Button(self.tutorial_frame, text="다음 ▶", font=("Arial", 12, "bold"),
                                  command=self.next_tutorial_page)
        self.next_btn.place(relx=0.9, rely=0.9, anchor="center")

        # ============================================
        # 3. 게임 화면
        # ============================================
        self.game_frame = tk.Frame(root)
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
        # 튜토리얼을 열 때 항상 첫 페이지(0)로 초기화
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
        # 1. 이미지 변경
        self.tut_label.config(image=self.tutorial_images[self.current_tut_page])

        # 2. 버튼 보이기/숨기기 처리
        # 첫 페이지면 '이전' 버튼 숨김
        if self.current_tut_page == 0:
            self.prev_btn.place_forget()
        else:
            self.prev_btn.place(relx=0.9, rely=0.9, anchor="center")  # 위치 재조정

        # 마지막 페이지면 '다음' 버튼 숨김
        if self.current_tut_page == len(self.tutorial_images) - 1:
            self.next_btn.place_forget()
        else:
            self.next_btn.place(relx=0.9, rely=0.9, anchor="center")  # 위치 재조정

    # ====== 게임 진행 함수 ======
    def start_game(self):
        self.cover_frame.pack_forget()
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

    def calculate_ai_score(self, target_word_kr):
        if self.model is None:
            return random.randint(30, 70)

        target_word_en = PROMPT_MAP.get(target_word_kr, "object")
        text_prompts = [
            f"a sketch of a {target_word_en}",
            "messy scribbles",
            "blank white paper",
            "text or writing"
        ]

        inputs = self.processor(text=text_prompts, images=self.image, return_tensors="pt", padding=True)
        with torch.no_grad():
            outputs = self.model(**inputs)

        probs = outputs.logits_per_image.softmax(dim=1)
        score_float = probs[0][0].item()

        final_score = int(score_float * 100)
        if final_score < 10: final_score = 10
        if final_score > 98: final_score = 100

        return final_score

    def check_answer(self):
        self.check_button.config(text="채점 중...", state="disabled")
        self.root.update()

        answer_kr = self.prompts[self.current_prompt_index]
        score = self.calculate_ai_score(answer_kr)

        self.check_button.config(text="만디에게 보여주기", state="normal")

        msg = f"점수: {score}점"
        if score > 85:
            msg += "\n우와! 정말 잘 그렸다요. 완벽하게 알아봤다요."
        elif score > 50:
            msg += "\n특징을 잘 잡은거다요! 대충 알겠다요!"
        else:
            msg += "\n미안하다요... 잘 모르겠다요..."

        messagebox.showinfo("만디의 생각", f"필요한 준비물: {answer_kr}\n{msg}")

        self.current_prompt_index += 1
        if self.current_prompt_index >= len(self.prompts):
            messagebox.showinfo("게임 종료", "모든 제시어 완료!")
            self.root.destroy()
            return

        self.prompt_label.config(text=f"필요한 준비물: {self.prompts[self.current_prompt_index]}")
        self.reset_canvas()


if __name__ == "__main__":
    root = tk.Tk()
    app = PaintGame(root)
    root.mainloop()