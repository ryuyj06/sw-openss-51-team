import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw

# ====== 기본 설정 ======
CANVAS_WIDTH = 600
CANVAS_HEIGHT = 400

# ====== 제시어 목록 ======
PROMPTS = ["사과", "고양이", "집", "나무", "자동차"]

class PaintGame:
    def __init__(self, root):
        self.root = root
        self.root.title("드로잉 교육 게임")

        # 현재 제시어 인덱스
        self.current_prompt_index = 0

        # ====== 제시어 라벨 ======
        self.prompt_label = tk.Label(root,
                                     text=f"제시어: {PROMPTS[self.current_prompt_index]}",
                                     font=("Arial", 18))
        self.prompt_label.pack(pady=10)

        # ====== 캔버스 ======
        self.canvas = tk.Canvas(root, bg="white",
                                width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
        self.canvas.pack(pady=5)

        # Pillow 이미지 버퍼
        self.image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "white")
        self.draw = ImageDraw.Draw(self.image)

        # ====== 마우스 이벤트 ======
        self.last_x, self.last_y = None, None
        self.canvas.bind("<ButtonPress-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw_line)

        # ====== 채점 버튼 ======
        self.check_button = tk.Button(root, text="채점하기", font=("Arial", 14),
                                      command=self.check_answer)
        self.check_button.pack(pady=10)

    # ----- 그림 그리기 시작 -----
    def start_draw(self, event):
        self.last_x, self.last_y = event.x, event.y

    # ----- 선 그리기 -----
    def draw_line(self, event):
        self.canvas.create_line(self.last_x, self.last_y,
                                event.x, event.y, fill="black", width=3)
        self.draw.line((self.last_x, self.last_y, event.x, event.y),
                       fill="black", width=3)
        self.last_x, self.last_y = event.x, event.y

    # ----- 그림 초기화 -----
    def reset_canvas(self):
        self.canvas.delete("all")
        self.image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "white")
        self.draw = ImageDraw.Draw(self.image)

    # ----- 점수 계산(기본 버전: 임의 점수) -----
    def calculate_dummy_score(self):
        import random
        return random.randint(40, 100)

    # ----- 채점하기 -----
    def check_answer(self):
        answer = PROMPTS[self.current_prompt_index]

        # 현재는 랜덤 점수(시스템 테스트용)
        score = self.calculate_dummy_score()

        # 결과 보여주기
        messagebox.showinfo("채점 결과",
                            f"제시어: {answer}\n점수: {score}점")

        # 다음 제시어로 이동
        self.current_prompt_index += 1

        if self.current_prompt_index >= len(PROMPTS):
            messagebox.showinfo("게임 종료", "모든 제시어를 완료했습니다!")
            self.root.destroy()
            return

        # 제시어 텍스트 업데이트
        self.prompt_label.config(text=f"제시어: {PROMPTS[self.current_prompt_index]}")

        # 캔버스 초기화
        self.reset_canvas()


# ====== 실행 ======
root = tk.Tk()
app = PaintGame(root)
root.mainloop()