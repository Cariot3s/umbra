document.addEventListener("DOMContentLoaded", () => {

    const door = document.getElementById("door");
    const loginBox = document.getElementById("login-box");
    const userInput = document.getElementById("user");
    const passInput = document.getElementById("pass");
    const loginBtn = document.getElementById("login-btn");

    let opened = false;

    door.addEventListener("click", () => {
        if (!opened) {
            opened = true;
            door.classList.add("open");

            setTimeout(() => {
                loginBox.classList.remove("hidden");
                userInput.focus();
            }, 600);
        }
    });

    async function tryLogin() {
        if (!opened) return;

        const user = userInput.value.trim();
        const pass = passInput.value.trim();

        if (!user || !pass) return;

        try {
            const res = await fetch("/api/validate_level8", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user, pass })
            });

            const data = await res.json();

            if (data.ok) {
                // Marcamos flag de nivel 8 completado
                UmbraState.setFlag("level8_completed");

                // Redirigimos al nivel 9
                window.location.href = "/escucha/index.html";
            } else {
                // Credenciales incorrectas
                userInput.value = "";
                passInput.value = "";
                userInput.focus();
            }
        } catch (e) {
            console.error("Error validando Level 8:", e);
        }
    }

    loginBtn.addEventListener("click", tryLogin);
    document.addEventListener("keydown", e => {
        if (e.key === "Enter") tryLogin();
    });

});
