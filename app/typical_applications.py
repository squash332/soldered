# DRAFT copy, not yet through the tone-of-voice review pass.
TYPICAL_APPLICATIONS: dict[str, str] = {
    "333232": (
        "Inkplate 6 suits projects that show information for long periods "
        "without draining a battery. You can build a room sign that updates "
        "its schedule once an hour, a weather display that pulls data over "
        "Wi-Fi, or a shelf label that shows stock counts. Because the "
        "e-paper display only draws power when the image changes, a single "
        "battery charge can run a display for weeks. Use the SD card slot "
        "to show a rotating set of images without a network connection, or "
        "use the qwiic port to add a sensor and show live readings. The "
        "ESP32 microcontroller and Arduino or MicroPython support make it "
        "straightforward to fetch data from an API and render it as text or "
        "a bitmap."
    ),
    "333352": (
        "NULA DeepSleep suits battery-powered projects that spend most of "
        "their time asleep and wake briefly to take a reading or send data. "
        "Typical uses include a remote temperature logger, a mailbox or "
        "door sensor that reports over Wi-Fi, or a battery-powered "
        "prototype that needs qwiic sensors without extra wiring. The "
        "onboard battery charger lets you run it directly from a LiPo cell "
        "and recharge over USB-C. Because it supports the Arduino IDE, "
        "MicroPython, and ESP-IDF, you can start with simple example code "
        "and move to lower-level control later if your project needs "
        "longer battery life."
    ),
    "333032": (
        "The SHTC3 breakout suits any project that needs to measure "
        "temperature and humidity over I2C. Use it in a room climate "
        "monitor, a greenhouse controller, or a weather station alongside "
        "other qwiic sensors. Its small size and low power draw make it a "
        "good fit for battery-powered and breadboard prototypes alike. The "
        "qwiic connector lets you chain it with other qwiic boards without "
        "soldering, while the breadboard-compatible header pins keep it "
        "usable in a standard breadboard layout. Read both temperature and "
        "humidity from a single sensor over a two-wire I2C bus."
    ),
}


def typical_applications(sku: str) -> str | None:
    return TYPICAL_APPLICATIONS.get(sku)
