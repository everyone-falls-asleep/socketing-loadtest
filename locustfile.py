import time
import requests
from locust import HttpUser, User, SequentialTaskSet, task, between
import socketio
import random
import os

TARGET_API_SERVER = os.getenv("TARGET_API_SERVER")
TARGET_QUEUE_SERVER = os.getenv("TARGET_QUEUE_SERVER")
TARGET_SOCKET_SERVER = os.getenv("TARGET_SOCKET_SERVER")
EVENT_ID = os.getenv("EVENT_ID")
EVENT_DATE_ID = os.getenv("EVENT_DATE_ID")

# class MyUser(HttpUser):
#     @task
#     def my_task(self):
#         self.client.get("/api/events")


class SocketIOUser(User):
    wait_time = between(1, 5)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 데이터 저장 변수 초기화
        self.areas = []
        self.seats = []
        self.selected_area_id = None

    def on_start(self):
        self.token = self.get_token()
        if not self.token:
            print("Failed to get token. Stopping user tasks.")
            self.stop()
            return

        # Socket.IO 클라이언트 초기화 및 연결
        self.sio = socketio.Client()

        # 좌석 데이터를 저장할 변수
        self.seats = []

        @self.sio.event
        def connect():
            print("Connected to the Socket.IO server")

        @self.sio.event
        def disconnect():
            print("Disconnected from the Socket.IO server")

        @self.sio.event
        def error(data):
            print(f"Error received from server: {data}")

        @self.sio.on("tokenIssued")
        def on_token_issued(data):
            # print(f"Received tokenIssued event: {data}")
            self.entranceToken = data.get("token")
            if self.entranceToken:
                self.connect_to_main_socket_server()

        @self.sio.on("updateQueue")
        def on_update_queue(data):
            pass
            # print(f"Received updateQueue event: {data}")

        # 서버 연결
        try:
            print(f"TARGET_QUEUE_SERVER: {TARGET_QUEUE_SERVER}")
            self.sio.connect(
                TARGET_QUEUE_SERVER,
                transports=["websocket"],
                auth={"token": self.token}
            )

            self.sio.emit("joinQueue", {
                "eventId": EVENT_ID,
                "eventDateId": EVENT_DATE_ID
            })
        except Exception as e:
            print(f"Connection exception: {e}")
            print("Stopping this user's tasks.")
            self.stop()

    def get_token(self):
        """
        로그인 요청을 통해 토큰을 가져옵니다.
        """
        login_url = f"{TARGET_API_SERVER}/api/auth/login"
        login_payload = {
            "email": "윤효전@jungle.com",
            "password": "123456"
        }

        try:
            print(f"Logging in at {login_url}")
            response = requests.post(login_url, json=login_payload)
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("code") == 0:  # 성공 코드 확인
                    token = response_data.get("data", {}).get("accessToken")
                    if token:
                        print(f"Successfully obtained token: {token}")
                        return token
                    else:
                        print("Token not found in response.")
                else:
                    print(
                        f"Login failed: "
                        f"{response_data.get('message', 'Unknown error')}"
                    )
            else:
                print(
                    f"Login failed with status code "
                    f"{response.status_code}: {response.text}"
                )
        except Exception as e:
            print(f"Error during login: {e}")
        return None

    def connect_to_main_socket_server(self):
        self.sio = socketio.Client()
        self.seats = []
        self.areas = []
        self.selected_area_id = None

        @self.sio.event
        def connect():
            print("Connected to the Main Socket.IO server")

        @self.sio.event
        def disconnect():
            print("Disconnected from the Main Socket.IO server")

        @self.sio.event
        def error(data):
            print(f"Error received from Main Socket.IO server: {data}")

        @self.sio.on("roomJoined")
        def on_room_joined(data):
            # print(f"Received roomJoined event: {data}")
            self.areas = data.get("areas", [])

        @self.sio.on("areaJoined")
        def on_area_joined(data):
            # print(f"Received areaJoined event: {data}")
            self.seats = data.get("seats", [])

        @self.sio.on("seatsSelected")
        def on_seat_selected(data):
            # print(f"Seat selection update: {data}")
            pass

        try:
            print(f"TARGET_SOCKET_SERVER: {TARGET_SOCKET_SERVER}")
            self.sio.connect(
                TARGET_SOCKET_SERVER,
                transports=["websocket"],
                auth={"token": self.entranceToken},
            )

            self.sio.emit("joinRoom", {
                "eventId": EVENT_ID,
                "eventDateId": EVENT_DATE_ID
            })

            # 랜덤 시간 대기
            disconnect_time = random.uniform(5, 15)
            print(f"Disconnecting in {disconnect_time:.2f} seconds...")
            time.sleep(disconnect_time)

            # 연결 종료
            self.sio.disconnect()
            print("Disconnected from Main Socket.IO server after random wait.")

            # 사용자 작업 중단
            print("Stopping this user's tasks.")
            self.stop()  # 현재 사용자만 중단
        except Exception as e:
            print(f"Main Socket.IO server connection exception: {e}")
            self.stop()

    @task
    def select_random_area_and_seat(self):
        # Step 1: 랜덤 Area 선택
        if not self.areas:
            print("No areas available to select. Ensure you have joined a room.")
            return

        selected_area = random.choice(self.areas)
        self.selected_area_id = selected_area.get("id", "")
        print(f"Selected area ID: {self.selected_area_id}")

        if not self.selected_area_id:
            print("Invalid area ID received from server.")
            return

        try:
            # 서버에 선택된 Area 요청
            self.sio.emit("joinArea", {
                "eventId": EVENT_ID,
                "eventDateId": EVENT_DATE_ID,
                "areaId": self.selected_area_id
            })

            # Step 2: 좌석 정보를 기다림
            time.sleep(1)  # 좌석 데이터가 수신될 때까지 잠시 대기
        except Exception as e:
            print(f"Error during area selection emit: {e}")
            return

        # Step 3: 랜덤 좌석 선택
        if not self.seats:
            print(f"No seats available in area ID {self.selected_area_id}.")
            return

        seat = random.choice(self.seats)
        seat_id = seat.get("id")
        print(f"Selected seat ID: {seat_id}")

        if seat_id:
            try:
                # 서버에 좌석 선택 요청
                self.sio.emit("selectSeats", {
                    "seatId": seat_id,
                    "eventId": EVENT_ID,
                    "eventDateId": EVENT_DATE_ID,
                    "areaId": self.selected_area_id
                })
                print(
                    f"Seat {seat_id} in area {self.selected_area_id} "
                    "selected successfully."
                )
            except Exception as e:
                print(f"Error during seat selection emit: {e}")
        else:
            print("Invalid seat ID received from server.")

    def on_stop(self):
        self.sio.disconnect()
