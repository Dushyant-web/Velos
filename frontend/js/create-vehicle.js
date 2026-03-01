// ================================
// Create Vehicle Page Logic
// ================================

requireAuth();

let isSubmitting = false;

const form = document.querySelector(".form-card");

if (form) {
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (isSubmitting) return;

        const submitBtn = document.querySelector(".submit-btn");

        const numberPlate = document.querySelector("#numberPlate").value.trim().toUpperCase();
        const name = document.querySelector("#vehicleName").value.trim();
        const model = document.querySelector("#model").value.trim();
        const year = parseInt(document.querySelector("#year").value);
        const imageUrl = document.querySelector("#imageUrl").value.trim();

        if (!numberPlate || !name || !model || !year) {
            showMessage("Please fill all required fields", "error");
            return;
        }

        isSubmitting = true;

        // Disable button + show spinner
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span class="spinner"></span> Creating...`;

        const payload = {
            number_plate: numberPlate,
            name: name,
            model: model,
            year: year,
            image_url: imageUrl || null
        };

        try {
            const response = await authFetch(`${BASE_URL}/vehicles`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json();
                showMessage(errorData.detail || "Vehicle may already exist", "error");
                resetButton(submitBtn);
                return;
            }

            showMessage("Vehicle created successfully!", "success");

            setTimeout(() => {
                window.location.href = "dashboard.html";
            }, 1200);

        } catch (err) {
            console.error(err);
            showMessage("Something went wrong", "error");
            resetButton(submitBtn);
        }
    });
}

function resetButton(button) {
    isSubmitting = false;
    button.disabled = false;
    button.innerHTML = "Create Vehicle";
}

const imageInput = document.querySelector("#imageUrl");

if (imageInput) {
    imageInput.addEventListener("input", () => {
        let preview = document.querySelector("#imagePreview");

        if (!preview) {
            preview = document.createElement("img");
            preview.id = "imagePreview";
            preview.style.marginTop = "15px";
            preview.style.width = "100%";
            preview.style.borderRadius = "12px";
            preview.style.objectFit = "cover";
            imageInput.parentElement.appendChild(preview);
        }

        preview.src = imageInput.value;
    });
}

// ================================
// Toast Message System
// ================================

function showMessage(message, type) {
    let toast = document.createElement("div");
    toast.innerText = message;

    toast.style.position = "fixed";
    toast.style.bottom = "30px";
    toast.style.right = "30px";
    toast.style.padding = "14px 20px";
    toast.style.borderRadius = "10px";
    toast.style.fontWeight = "600";
    toast.style.zIndex = "9999";
    toast.style.transition = "0.3s ease";
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";

    if (type === "success") {
        toast.style.background = "#00ff88";
        toast.style.color = "#000";
    } else {
        toast.style.background = "#ff4d4d";
        toast.style.color = "#fff";
    }

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "1";
        toast.style.transform = "translateY(0)";
    }, 10);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(10px)";
        setTimeout(() => toast.remove(), 300);
    }, 2500);
}

