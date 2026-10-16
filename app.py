
import math
import time

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Ellipse, FancyArrowPatch, Circle

st.set_page_config(
    page_title="성층권 비행 시뮬레이터",
    page_icon="✈️",
    layout="wide"
)

st.title("✈️ 성층권 비행 시뮬레이터")
st.caption("쌍발 터보팬 여객기 | 양력 · 중력 · 항력 · 추력")

G = 9.80665
WING_AREA = 124.0
CD0 = 0.022
INDUCED_K = 0.045
MAX_THRUST = 240000.0
DT = 0.5

with st.sidebar:
    st.header("비행 조건")

    mass = st.slider(
        "항공기 질량 (kg)", 40000, 100000, 70000, 5000
    )
    initial_speed = st.slider(
        "초기 속도 (m/s)", 120, 280, 230, 10
    )
    throttle = st.slider(
        "터보팬 엔진 출력 (%)", 40, 100, 90, 5
    )
    aoa = st.slider(
        "받음각 (도)", 2.0, 10.0, 4.0, 0.5
    )
    duration = st.slider(
        "비행 시간 (분)", 2, 30, 15
    )

    st.info("교육용 근사 물리 모델입니다.")

def air_density(h):
    h = max(0.0, min(h, 30000.0))
    return 1.225 * math.exp(-h / 8500.0)

def calculate_forces(speed, altitude):
    rho = air_density(altitude)
    dynamic_pressure = 0.5 * rho * speed**2

    cl = max(0.12, min(0.75, 0.08 + 0.025 * aoa))
    cd = CD0 + INDUCED_K * cl**2

    lift = dynamic_pressure * WING_AREA * cl
    drag = dynamic_pressure * WING_AREA * cd
    weight = mass * G

    thrust = MAX_THRUST * throttle / 100
    thrust *= max(0.20, rho / 1.225)

    return lift, weight, drag, thrust, rho

def create_aircraft_diagram():
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    # 동체
    fuselage = Polygon(
        [(0.8, 3), (1.5, 3.25), (7.8, 3.25),
         (9.2, 3), (7.8, 2.75), (1.5, 2.75)],
        closed=True, facecolor="#e8edf2",
        edgecolor="#34495e", linewidth=1.5
    )
    ax.add_patch(fuselage)

    # 주날개
    ax.add_patch(Polygon(
        [(3.8, 3.1), (4.7, 4.6), (5.7, 4.6),
         (5.25, 3.05), (7.1, 2.88),
         (5.0, 2.5), (4.2, 2.72)],
        closed=True, facecolor="#b8c9dc",
        edgecolor="#34495e"
    ))

    # 꼬리날개
    ax.add_patch(Polygon(
        [(1.5, 3.1), (1.8, 3.9), (2.3, 3.9),
         (2.25, 3.05), (2.9, 2.9), (2.0, 2.75)],
        closed=True, facecolor="#b8c9dc",
        edgecolor="#34495e"
    ))

    # 수직 꼬리날개
    ax.add_patch(Polygon(
        [(1.45, 3.1), (1.18, 4.4),
         (1.68, 4.4), (2.05, 3.12)],
        closed=True, facecolor="#b8c9dc",
        edgecolor="#34495e"
    ))

    # 터보팬 엔진 2기
    for x in [4.65, 5.65]:
        ax.add_patch(Ellipse(
            (x, 2.42), 0.82, 0.42,
            facecolor="#8797a8", edgecolor="#34495e"
        ))

    # 객실 창문
    for x in np.linspace(2.1, 7.3, 18):
        ax.add_patch(Circle((x, 3.08), 0.045, color="#3285a8"))

    # 힘의 방향 표시
    arrows = [
        ((5, 3.7), (5, 5.35), "양력 L", "green"),
        ((5, 2.55), (5, 0.75), "중력 W", "red"),
        ((4.1, 3), (1.65, 3), "항력 D", "orange"),
        ((6, 3), (8.85, 3), "추력 T", "blue")
    ]

    for start, end, label, color in arrows:
        ax.add_patch(FancyArrowPatch(
            start, end, arrowstyle="-|>",
            mutation_scale=16, linewidth=2.3, color=color
        ))
        ax.text(
            (start[0] + end[0]) / 2,
            (start[1] + end[1]) / 2 + 0.2,
            label, color=color, ha="center", fontsize=10
        )

    ax.text(
        5, 5.8, "쌍발 터보팬 여객기 구조 개념도",
        ha="center", fontsize=11
    )

    return fig

def simulate():
    speed = float(initial_speed)
    altitude = 0.0
    gamma = 0.0
    distance = 0.0
    elapsed = 0.0
    records = []

    total_steps = int(duration * 60 / DT)

    for i in range(total_steps + 1):
        lift, weight, drag, thrust, rho = calculate_forces(
            speed, altitude
        )

        if i % 2 == 0:
            records.append({
                "시간 (분)": elapsed / 60,
                "고도 (km)": altitude / 1000,
                "거리 (km)": distance / 1000,
                "속도 (m/s)": speed,
                "상승률 (m/s)": speed * math.sin(gamma),
                "양력 (kN)": lift / 1000,
                "중력 (kN)": weight / 1000,
                "항력 (kN)": drag / 1000,
                "추력 (kN)": thrust / 1000
            })

        alpha = math.radians(aoa)

        # 비행 경로 방향의 가속도
        acceleration = (
            thrust * math.cos(alpha)
            - drag
            - weight * math.sin(gamma)
        ) / mass

        # 비행 경로 각도의 변화율
        gamma_rate = (
            lift + thrust * math.sin(alpha)
            - weight * math.cos(gamma)
        ) / (mass * max(speed, 1))

        speed = max(70, min(330, speed + acceleration * DT))
        gamma += gamma_rate * DT
        gamma = max(
            math.radians(-12),
            min(math.radians(25), gamma)
        )

        altitude += speed * math.sin(gamma) * DT
        distance += speed * math.cos(gamma) * DT
        elapsed += DT

        altitude = max(0, min(50000, altitude))

        if altitude >= 50000:
            break

    return pd.DataFrame(records)

# 시뮬레이션 실행
df = simulate()
last = df.iloc[-1]

# 핵심 수치
c1, c2, c3, c4 = st.columns(4)

c1.metric("최종 고도", f"{last['고도 (km)']:.2f} km")
c2.metric("최종 속도", f"{last['속도 (m/s)']:.1f} m/s")
c3.metric("수평 이동 거리", f"{last['거리 (km)']:.1f} km")
c4.metric("최대 고도", f"{df['고도 (km)'].max():.2f} km")

left, right = st.columns(2)

with left:
    st.subheader("비행 고도 그래프")

    fig, ax = plt.subplots(figsize=(7, 4))

    ax.axhspan(
        12, 50, alpha=0.15,
        color="skyblue", label="성층권"
    )

    ax.axhline(12, linestyle="--", color="gray")
    ax.plot(
        df["시간 (분)"], df["고도 (km)"],
        linewidth=2.5, label="비행 고도"
    )

    ax.set_xlabel("시간 (분)")
    ax.set_ylabel("고도 (km)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    st.pyplot(fig)
    plt.close(fig)

with right:
    st.subheader("비행기 구조와 힘")
    st.pyplot(create_aircraft_diagram())
    plt.close("all")

st.subheader("네 가지 힘의 크기")

force_columns = st.columns(4)

force_data = [
    ("양력", "양력 (kN)", "🟢"),
    ("중력", "중력 (kN)", "🔴"),
    ("항력", "항력 (kN)", "🟠"),
    ("추력", "추력 (kN)", "🔵")
]

for col, (name, key, emoji) in zip(force_columns, force_data):
    col.metric(emoji + " " + name, f"{last[key]:.1f} kN")

st.subheader("시간에 따른 힘의 변화")

fig, ax = plt.subplots(figsize=(10, 4))

for key, label in [
    ("양력 (kN)", "양력"),
    ("중력 (kN)", "중력"),
    ("항력 (kN)", "항력"),
    ("추력 (kN)", "추력")
]:
    ax.plot(df["시간 (분)"], df[key], label=label)

ax.set_xlabel("시간 (분)")
ax.set_ylabel("힘 (kN)")
ax.grid(True, alpha=0.3)
ax.legend(ncol=4)

st.pyplot(fig)
plt.close(fig)

with st.expander("물리 공식 설명"):
    st.latex(r"L = \frac{1}{2}\rho V^2 S C_L")
    st.write("양력: 날개 주변의 공기 흐름으로 발생하는 힘")

    st.latex(r"D = \frac{1}{2}\rho V^2 S C_D")
    st.write("항력: 비행기의 운동을 방해하는 공기 저항")

    st.latex(r"W = mg")
    st.write("중력: 지구가 비행기를 끌어당기는 힘")

    st.latex(r"\sum F = ma")
    st.write("뉴턴 제2법칙: 알짜힘에 따라 가속도가 결정됨")


import plotly.graph_objects as go
import streamlit as st
import numpy as np

# 예시 비행 경로: 거리(km), 고도(km)
distance = np.linspace(0, 180, 61)
altitude = 11 * (1 - np.exp(-distance / 35))

fig = go.Figure(
    data=[
        go.Scatter(
            x=distance,
            y=altitude,
            mode="lines",
            line=dict(width=3),
            name="비행 경로"
        ),
        go.Scatter(
            x=[distance[0]],
            y=[altitude[0]],
            mode="text",
            text=["✈️"],
            textfont=dict(size=30),
            name="터보팬 여객기"
        )
    ]
)

frames = []
for i in range(len(distance)):
    frames.append(
        go.Frame(
            data=[
                go.Scatter(
                    x=distance[:i+1],
                    y=altitude[:i+1],
                    mode="lines",
                    line=dict(width=3)
                ),
                go.Scatter(
                    x=[distance[i]],
                    y=[altitude[i]],
                    mode="text",
                    text=["✈️"],
                    textfont=dict(size=30)
                )
            ],
            name=str(i)
        )
    )

fig.frames = frames

fig.update_layout(
    title="✈️ 성층권을 향해 비행하는 여객기",
    xaxis_title="비행 거리 (km)",
    yaxis_title="고도 (km)",
    xaxis=dict(range=[0, 180]),
    yaxis=dict(range=[0, 13]),
    height=500,
    updatemenus=[{
        "type": "buttons",
        "buttons": [
            {
                "label": "▶ 비행 시작",
                "method": "animate",
                "args": [
                    None,
                    {
                        "frame": {"duration": 100, "redraw": True},
                        "transition": {"duration": 0},
                        "fromcurrent": True
                    }
                ]
            },
            {
                "label": "⏸ 정지",
                "method": "animate",
                "args": [
                    [None],
                    {
                        "frame": {"duration": 0, "redraw": False},
                        "mode": "immediate"
                    }
                ]
            }
        ]
    }]
)

st.plotly_chart(fig, use_container_width=True)

st.warning(
    "이 시뮬레이션은 교육용 근사 모델입니다. "
    "실제 항공기의 성능이나 안전성을 예측하는 데 사용하지 마세요."
)
