from locust import HttpUser, User, task, between
import socketio
import random
import os

TARGET_API_SERVER = os.getenv("TARGET_API_SERVER")
TARGET_SOCKET_SERVER = os.getenv("TARGET_SOCKET_SERVER")
EVENT_ID = os.getenv("EVENT_ID")
EVENT_DATE_ID = os.getenv("EVENT_DATE_ID")


# class MyUser(HttpUser):
#     @task
#     def my_task(self):
#         self.client.get("/api/events")


class SocketIOUser(User):
    wait_time = between(1, 5)

    def on_start(self):
        # Socket.IO 클라이언트 초기화 및 연결
        self.sio = socketio.Client()

        # 좌석 데이터를 저장할 변수
        self.seats = []

        @self.sio.event
        def connect():
            print("Connected to the Socket.IO server")

        @self.sio.event
        def connect():
            print("Connected to the Socket.IO server")

        @self.sio.event
        def disconnect():
            print("Disconnected from the Socket.IO server")

        @self.sio.event
        def error(data):
            print(f"Error received from server: {data}")

        @self.sio.on("roomJoined")
        def on_room_joined(data):
            # 서버로부터 수신한 데이터 처리 및 저장
            print(f"Received roomJoined event: {data}")
            self.seats = data.get("seats", [])  # 좌석 데이터 저장

        @self.sio.on("seatSelected")
        def on_seat_selected(data):
            # 서버로부터 좌석 선택 상태 변경 브로드캐스트를 받음
            print(f"Seat selection update: {data}")

        # 서버 연결
        try:
            print(f"TARGET_SOCKET_SERVER: {TARGET_SOCKET_SERVER}")
            self.sio.connect(TARGET_SOCKET_SERVER, transports=["websocket"])
        except Exception as e:
            print(f"Connection exception: {e}")

    @task
    def join_room(self):
        print(f"Event ID: {EVENT_ID} and Event Date ID: {EVENT_DATE_ID}")
        event_data = {
            "eventId": EVENT_ID,
            "eventDateId": EVENT_DATE_ID
        }
        try:
            self.sio.emit("joinRoom", event_data)
            print(f"Sent joinRoom event with data: {event_data}")
        except Exception as e:
            print(f"Error during emit: {e}")

    @task
    def select_random_seat(self):
        # 좌석 정보를 기반으로 랜덤 좌석 선택
        if not self.seats:
            print("No seats available to select. Ensure you have joined a room.")
            return

        seat = random.choice(self.seats)  # 랜덤하게 좌석 선택
        seat_id = seat.get("id")
        if seat_id:
            try:
                event_data = {
                    "seatId": seat_id,
                    "eventId": EVENT_ID,
                    "eventDateId": EVENT_DATE_ID
                }
                self.sio.emit("selectSeat", event_data)
                print(f"Sent selectSeat event with data: {event_data}")
            except Exception as e:
                print(f"Error during seat selection emit: {e}")
        else:
            print("Invalid seat ID received from server.")

    def on_stop(self):
        self.sio.disconnect()
