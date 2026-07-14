from .servo_board import ServoBoardInterface

# Wenn sich die Datei im gleichen Ordner befindet:
# from serial_interface import ServoBoardInterface
import time

SERVO = 1


def main():
    # 1. Initialisiere die Verbindung (Port anpassen!)
    # Wichtig: Der Timeout und der Buffer im Interface sorgen für Stabilität
    servo_board = ServoBoardInterface(port="/dev/ttyUSB0", baudrate=115200)

    time.sleep(2)  # Warten, bis der Arduino bereit ist (nach Reset durch Serial)

    print("--- Servo Steuerung gestartet ---")

    # BESP: Servo 1 auf 90 Grad bewegen
    print("Bewege Servo 1 auf 90 Grad...")
    servo_board.move_servo(SERVO, 90)

    time.sleep(2)

    # BESP: Servo 1 auf 0 Grad zurück (Reset)
    print("Bewege Servo 1 auf 0 Grad...")
    servo_board.reset_servo_pose(1)

    # BESP: Sweep von 0 bis 180
    print("Sweep von 0 bis 180 Grad...")
    servo_board.sweep_servo(SERVO, 0, 180)

    # BESP: LED Farbe ändern
    # print("Setze LED auf Rot...")
    # servo_board.send_cmd_to_board("led_color red")

    # Wichtig: Sauberes Beenden
    servo_board.thread_close()
    print("Fertig.")


if __name__ == "__main__":
    main()
