# sw-openss-51-team

# 🧠 사물 인식 능력 향상을 위한 AI 드로잉 학습 프로그램

본 프로그램은 영유아 및 지적장애인의 **사물 인식 능력**과 **개념 표현 능력**을 향상시키기 위해 만들어진  
AI 기반 교육 프로그램입니다.

이 프로그램은 대상자가 그린 그림을 인공지능이 분석하여  
**주어진 단어(사물 이름)와 얼마나 유사한지 점수로 평가**합니다.  
또한 학습 효과를 방해하는 **부정행위(글씨 쓰기)**를 AI가 자동으로 감지하여 차단합니다.

---

## 🎯 개발 목적

영유아와 지적장애인은 사물을 보고 **직접 그려보는 과정**이  
인지 발달과 학습 효과에 매우 중요합니다.

실제로 본 프로그램은 단순히 ‘그림을 완성하는 것’을 넘어, 다음과 같은 발달적 이점을 제공합니다.

1. 시각 정보 처리 능력 향상
사물의 형태·색·특징을 관찰하고 머릿속에서 다시 구성하는 과정은
시지각 발달을 촉진합니다.

2. 언어와 시각 개념의 연결 강화
단어(텍스트)로만 이해하는 것이 아니라,
실제 이미지 형태로 개념을 연결하여 장기 기억 형성에 도움을 줍니다.

3. 소근육 및 운동 협응 발달
손을 움직여 그림을 그리는 활동은 손가락·손목의 조절 능력을 높이고
일상생활 동작에 필요한 협응 능력 향상에도 긍정적인 영향을 줍니다.

4. 자기 표현력 증진
그림을 통해 자신이 이해한 사물을 표현하면서
자기 주도적 학습과 창의적 사고가 자라납니다.

5. 정확한 사물 인식 학습
눈으로 보고 → 머릿속에서 해석하고 → 손으로 표현하는 일련의 순환 과정은
사물 인식 능력을 자연스럽게 강화합니다.

6. 단어 학습
AI 모델이 제시하는 점수를 통해 건강한 경쟁심을 유도하고,
그 과정에서 자기주도적으로 학습에 참여하도록 돕습니다.
(적은 확률로 고난이도의 단어가 등장합니다.)

---

## ✨ 주요 기능

### 1. 🖼️ AI 기반 그림 인식 (CLIP 모델)

- Hugging Face 오픈소스 모델 **openai/clip-vit-base-patch32** 사용  
- 아이가 그린 그림을 인공지능이 분석하여 목표 단어와의 유사도를 계산  
- 그림과 텍스트의 특징을 동시에 이해하는 CLIP의 장점을 활용

  ## 🧩 Main Code(🖼1.의 로직)
  ```python
  target_word_en = PROMPT_MAP.get(target_word_kr, "object") # [0] 그림, [1] 정답 단어 글씨(함정), [2-3] 일반 글씨, [4-5] 무의미
  text_prompts = [
    f"a sketch of a {target_word_en}", # 0
    f"the written word '{target_word_en}'", # 1
    "written text", # 2
    "handwriting and letters", # 3
    "messy scribbles", # 4
    "blank white paper" # 5
  ]
  
  inputs = self.processor(text=text_prompts, images=self.image, return_tensors="pt", padding=True)
  with torch.no_grad():
    outputs = self.model(**inputs)
  probs = outputs.logits_per_image.softmax(dim=1)[0]
  
  prob_drawing = probs[0].item()
  prob_word_text = probs[1].item()
  prob_general_text = probs[2].item() + probs[3].item() #점수 계산식 1
  total_text_prob = prob_word_text + prob_general_text #점수 계산식 2
  final_score = int(prob_drawing * 100) #점수 계산식3
---

### 2. 🚫 부정행위(글씨 쓰기) 자동 감지

AI(CLIP)는 이미지 속 텍스트·문자 형태를 식별할 수 있으며, 다음과 같은 경우를 감지합니다:

- 사물 이름을 그대로 적어 넣는 경우  
- 알파벳 또는 한글 형태가 명확한 텍스트를 쓰는 경우  
- 그림 대신 문자 기반 낙서를 하는 경우  

감지 시:

- 점수를 크게 감소  
- "만디는 글씨를 읽지 못해요!" 등의 메시지로 바른 학습 방향 제시  

  ## 🧩 Main Code(🚫2.의 로직)
   ```python
        prob_general_text = probs[2].item() + probs[3].item() #점수 계산식 1
        total_text_prob = prob_word_text + prob_general_text #점수 계산식 2
        
            if total_text_prob > prob_drawing or total_text_prob > 0.25: #점수 계산식 @
            print(">> 글씨 감지됨! 점수 대폭 삭감")
            final_score = min(20, int(final_score * 0.2))

        if final_score < 10: final_score = 10
        if final_score > 98: final_score = 100

이는 그림을 통해 사물을 인식하는 **학습 과정 자체를 보호**하기 위한 핵심 기능입니다.

---

### 3. 🎵 소리, 버튼, GUI 지원

- Tkinter 기반 GUI 제공
- Pygame으로 효과음 출력(배경음악: 동물의 숲 mainlobby ost)
- 아이들이 쉽게 사용할 수 있는 직관적인 인터페이스(배경화면, 도움말, 간단한 팝업 메시지등)

---

## 🛠 사용된 기술

| 구성 | 기술 |
|------|------|
| GUI | Tkinter |
| 사운드 | Pygame |
| AI 모델 | Hugging Face Transformers (CLIP) |
| AI 연산 | PyTorch |
| 이미지 처리 | Pillow(PIL) |

---

## 📦 버전 및 패키지 정보

### 1. Python 버전
- Python **3.8 이상 권장**

---

### 2. 필요한 패키지 설치

아래 4개의 패키지만 설치하면 실행 가능합니다.

```bash
pip install pillow
pip install pygame
pip install torch
pip install transformers
