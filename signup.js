const userData = {
    latitude: null,
    longitude: null,
    email: null,
    password: null,
    nickname: null
};

function showStep(n) {
    document.querySelectorAll(".step")
        .forEach(s => s.classList.remove("active"));
    document.getElementById("step" + n).classList.add("active");
}

// STEP 1: 位置情報
document.getElementById("allowLocation").addEventListener("click", () => {
    if (!navigator.geolocation) {
        alert("位置情報に対応していません");
        return;
    }

    navigator.geolocation.getCurrentPosition(
        pos => {
            userData.latitude = pos.coords.latitude;
            userData.longitude = pos.coords.longitude;
            showStep(2);
        },
        () => {
            alert("位置情報を取得できませんでした");
        }
    );
});

// STEP 2 → STEP 3
document.getElementById("toStep3").addEventListener("click", () => {
    userData.email = document.getElementById("email").value;
    userData.password = document.getElementById("password").value;
    showStep(3);
});

// STEP 3: 送信
document.getElementById("submit").addEventListener("click", async () => {
    userData.nickname = document.getElementById("nickname").value;

    const res = await fetch("/signup", {   // ← ここ重要
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(userData)
    });

    const html = await res.text();
    document.open();
    document.write(html);
    document.close();
});
