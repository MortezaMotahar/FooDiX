/* ===========================================
            FooDiX MoSCoW Board
=========================================== */

// ===========================================
// Language Switch
// ===========================================

const languageButton = document.getElementById("languageButton");

let currentLanguage = "fa";

languageButton.addEventListener("click", () => {

    currentLanguage = currentLanguage === "fa"
        ? "en"
        : "fa";

    document.documentElement.lang = currentLanguage;

    document.documentElement.dir =
        currentLanguage === "fa"
        ? "rtl"
        : "ltr";

    languageButton.innerHTML =
        currentLanguage === "fa"
        ? "English"
        : "فارسی";

    document.querySelectorAll(".lang").forEach(item => {

        item.textContent =
            item.dataset[currentLanguage];

    });

});
// ===========================================
// Animated Badge Counter
// ===========================================

const badges = document.querySelectorAll(".badge");

badges.forEach(badge => {

    const target = Number(badge.textContent);

    let count = 0;

    badge.textContent = "0";

    const timer = setInterval(() => {

        count++;

        badge.textContent = count;

        if (count >= target) {

            clearInterval(timer);

        }

    }, 120);

});
// ===========================================
// Progress Animation
// ===========================================

window.addEventListener("load", () => {

    document.querySelectorAll(".fill").forEach(bar => {

        const width = bar.style.width;

        bar.style.width = "0";

        setTimeout(() => {

            bar.style.transition =
                "width 1.6s ease";

            bar.style.width = width;

        }, 200);

    });

});
// ===========================================
// Card Hover Effect
// ===========================================

const cards = document.querySelectorAll(".column");

cards.forEach(card => {

    card.addEventListener("mouseenter", () => {

        card.style.transition =
            "transform .35s ease, box-shadow .35s ease";

    });

    card.addEventListener("mousemove", (e) => {

        const rect = card.getBoundingClientRect();

        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const rotateX = ((rect.height / 2 - y) / 18);
        const rotateY = ((x - rect.width / 2) / 18);

        card.style.transform =`
            perspective(1000px)
             rotateX(${rotateX}deg)
             rotateY(${rotateY}deg)
             translateY(-8px)`;

    });

    card.addEventListener("mouseleave", () => {

        card.style.transform =
            "perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0)";

    });

});

// ===========================================
// Ripple Effect
// ===========================================

cards.forEach(card => {

    card.addEventListener("click", function (e) {

        const ripple = document.createElement("span");

        const rect = this.getBoundingClientRect();

        const size = Math.max(rect.width, rect.height);

        ripple.style.width = size + "px";
        ripple.style.height = size + "px";

        ripple.style.left =
            (e.clientX - rect.left - size / 2) + "px";

        ripple.style.top =
            (e.clientY - rect.top - size / 2) + "px";

        ripple.style.position = "absolute";
        ripple.style.borderRadius = "50%";
        ripple.style.background = "rgba(255,255,255,.25)";
        ripple.style.pointerEvents = "none";
        ripple.style.transform = "scale(0)";
        ripple.style.transition = ".6s";
        ripple.style.opacity = "1";

        this.appendChild(ripple);

        requestAnimationFrame(() => {

            ripple.style.transform = "scale(2)";
            ripple.style.opacity = "0";

        });

        setTimeout(() => {

            ripple.remove();

        }, 600);

    });

});

// ===========================================
// Fade In List Items
// ===========================================

const observer = new IntersectionObserver(entries => {

    entries.forEach(entry => {

        if (entry.isIntersecting) {

            entry.target.style.opacity = "1";

            entry.target.style.transform =
                "translateY(0)";

        }

    });

});

document.querySelectorAll(".column li").forEach(item => {

    item.style.opacity = "0";

    item.style.transform = "translateY(20px)";

    item.style.transition = ".5s ease";

    observer.observe(item);

});
/* ===========================================
        Save Selected Language
=========================================== */

//*const savedLanguage = localStorage.getItem("foodix-language");

//if (savedLanguage) {

    //currentLanguage = savedLanguage;

    //document.documentElement.lang = currentLanguage;

    //document.documentElement.dir =
        //currentLanguage === "fa"
            //? "rtl"
            //: "ltr";

    //languageButton.innerHTML =
        //currentLanguage === "fa"
            //? "English"
            //: "فارسی";

    //document.querySelectorAll(".lang").forEach(item => {

        //item.textContent = item.dataset[currentLanguage];

    //});

//}

languageButton.addEventListener("click", () => {

    localStorage.setItem(
        "foodix-language",
        currentLanguage
    );

});


/* ===========================================
            Aurora Parallax
=========================================== */

const aurora = document.querySelectorAll(".aurora span");

document.addEventListener("mousemove", e => {

    const x = e.clientX / window.innerWidth;

    const y = e.clientY / window.innerHeight;

    aurora.forEach((blob, index) => {

        const speed = (index + 1) * 15;

        blob.style.transform =`
            translate(${x * speed}px, ${y * speed}px)`;

    });

});


/* ===========================================
            Welcome Animation
=========================================== */

window.addEventListener("load", () => {

    document.body.animate(

        [

            {

                opacity: 0

            },

            {

                opacity: 1

            }

        ],

        {

            duration: 700,

            fill: "forwards"

        }

    );

});


/* ===========================================
            Console Signature
=========================================== */

console.log(

    "%c FooDiX MoSCoW Board ",

    "background:#2563eb;color:white;padding:10px 20px;border-radius:8px;font-size:16px;font-weight:bold;"

);

console.log(

    "%cDesigned & Developed by Morteza Motahar",

    "color:#22c55e;font-size:14px;font-weight:bold;"

);


/* ===========================================
        Keyboard Shortcut (L)
=========================================== */

document.addEventListener("keydown", e => {

    if (e.key.toLowerCase() === "l") {

        languageButton.click();

    }

});