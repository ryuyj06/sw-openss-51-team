import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageTk
import pygame
import random

# ====== AI 관련 라이브러리 ======
import torch
from transformers import CLIPProcessor, CLIPModel
import threading  # 로딩 중 렉 방지용 (선택적)

# ====== 기본 설정 ======
CANVAS_WIDTH = 600
CANVAS_HEIGHT = 400

# ====== 전체 제시어 (한국어) ======
ALL_PROMPTS = [
    "사과", "고양이", "집", "나무", "자동차",
    "물고기", "강아지", "꽃", "비행기", "컵"
]

# ====== AI 인식을 위한 한영 변환 딕셔너리 ======
# CLIP 모델은 영어 프롬프트에서 성능이 더 좋으므로 매핑해줍니다.
PROMPT_MAP = {
    "사과": "apple",
    "고양이": "cat",
    "집": "house",
    "나무": "tree",
    "자동차": "car",
    "물고기": "fish",
    "강아지": "puppy",
    "꽃": "flower",
    "비행기": "airplane",
    "컵": "cup"
}


class PaintGame:
    def __init__(self, root):
        self.root = root
        self.root.title("AI 드로잉 교육 게임")
        self.root.resizable(False, False)

        # ============================================
        # AI 모델 로딩 (시간이 걸리므로 안내 메시지 출력)
        # ============================================
        print("AI 모델을 로딩 중입니다... 잠시만 기다려주세요.")
        try:
            # OpenAI의 CLIP 모델 사용 (이미지와 텍스트의 유사도 측정에 탁월)
            self.model_name = "openai/clip-vit-base-patch32"
            self.model = CLIPModel.from_pretrained(self.model_name)
            self.processor = CLIPProcessor.from_pretrained(self.model_name)
            print("AI 모델 로딩 완료!")
        except Exception as e:
            print(f"AI 모델 로딩 실패: {e}")
            self.model = None

        # ============================================
        # 음악 재생 (pygame)
        # ============================================
        pygame.mixer.init()
        try:
            pygame.mixer.music.load("animalforest.mp3")
            pygame.mixer.music.play(-1)
        except:
            print("음악 파일을 찾을 수 없습니다. (animalforest.mp3)")

        # ============================================
        # 표지 화면
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

        self.cover_button = tk.Button(self.cover_frame, text="시작", font=("Arial", 20),
                                      command=self.start_game)
        self.cover_button.place(relx=0.5, rely=0.8, anchor="center")

        # ============================================
        # 게임 화면 구성
        # ============================================
        self.game_frame = tk.Frame(root)
        self.prompts = random.sample(ALL_PROMPTS, 5)
        self.current_prompt_index = 0

        self.prompt_label = tk.Label(
            self.game_frame,
            text=f"제시어: {self.prompts[self.current_prompt_index]}",
            font=("Arial", 18)
        )

        try:
            bg_img = Image.open("maingame.jpg")
            bg_img = bg_img.resize((CANVAS_WIDTH, CANVAS_HEIGHT))
            self.bg_photo = ImageTk.PhotoImage(bg_img)
        except:
            self.bg_photo = None

        self.canvas = tk.Canvas(self.game_frame, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white")
        if self.bg_photo:
            self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        # Pillow 버퍼 (AI에게 보낼 순수한 그림 데이터)
        self.image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "white")
        self.draw = ImageDraw.Draw(self.image)

        self.last_x, self.last_y = None, None
        self.canvas.bind("<ButtonPress-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw_line)

        self.check_button = tk.Button(self.game_frame, text="만디에게 보여주기", font=("Arial", 14),
                                      command=self.check_answer)

    def start_game(self):
        self.cover_frame.pack_forget()
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

    # ============================================
    # ★ 핵심: AI 채점 로직
    # ============================================
    def calculate_ai_score(self, target_word_kr):
        if self.model is None:
            return random.randint(30, 70)  # 모델 로드 실패 시 랜덤 점수

        # 1. 한국어 제시어를 영어로 변환
        target_word_en = PROMPT_MAP.get(target_word_kr, "object")

        # 2. 비교할 텍스트 리스트 생성
        # AI에게 "이 그림이 [제시어 그림]인가요, 아니면 [낙서]나 [빈 종이]인가요?"라고 물어보는 방식
        text_prompts = [
            f"a sketch of a {target_word_en}",  # 정답 (예: a sketch of a cat)
            "messy scribbles",  # 오답 1 (낙서)
            "blank white paper",  # 오답 2 (빈 종이)
            "text or writing"  # 오답 3 (글씨)
        ]

        # 3. 모델 입력 처리
        inputs = self.processor(
            text=text_prompts,
            images=self.image,
            return_tensors="pt",
            padding=True
        )

        # 4. 추론 (유사도 계산)
        with torch.no_grad():  # 그래디언트 계산 안함 (속도 향상)
            outputs = self.model(**inputs)

        # 5. 확률 계산 (Softmax)
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1)  # 확률로 변환 (0.0 ~ 1.0)

        # 첫 번째 텍스트(정답 프롬프트)와의 일치 확률 가져오기
        score_float = probs[0][0].item()

        # 6. 점수 보정 (0~100점)
        # AI가 100% 확신하는 경우는 드물어서 약간의 보정을 해줍니다.
        final_score = int(score_float * 100)

        # 너무 낮은 점수 방지 (게임의 재미를 위해)
        if final_score < 10: final_score = 10
        if final_score > 98: final_score = 100

        return final_score

    def check_answer(self):
        # UI 반응성을 위해 채점 중이라는 메시지를 잠깐 띄우거나, 버튼을 비활성화 할 수 있습니다.
        self.check_button.config(text="채점 중...", state="disabled")
        self.root.update()

        answer_kr = self.prompts[self.current_prompt_index]

        # AI 점수 계산 호출
        score = self.calculate_ai_score(answer_kr)

        # 버튼 복구
        self.check_button.config(text="만디에게 보여주기", state="normal")

        # 결과 출력 (메시지에 따라 칭찬 문구 변경)
        msg = f"점수: {score}점"
        if score > 85:
            msg += "\n 우와! 정말 잘 그렸다요. 완벽하게 알아봤다요."
        elif score > 50:
            msg += "\n 이 정도면 특징을 잘 잡은거다요!"
        else:
            msg += "\n 다음에는 조금 더 자세히 그려보는거다요."

        messagebox.showinfo("AI 채점 결과", f"제시어: {answer_kr}\n{msg}")

        self.current_prompt_index += 1

        if self.current_prompt_index >= len(self.prompts):
            messagebox.showinfo("게임 종료", "모든 제시어 완료!")
            self.root.destroy()
            return

        self.prompt_label.config(
            text=f"제시어: {self.prompts[self.current_prompt_index]}"
        )
        self.reset_canvas()


# ===== 실행 =====
if __name__ == "__main__":
    root = tk.Tk()
    app = PaintGame(root)
    root.mainloop()