document.getElementById("crop-form").addEventListener("submit", async function(e) {
    e.preventDefault();

    document.getElementById("loading").style.display = "block";  // Show loading

    const city = document.getElementById("city").value;
    const soil = document.getElementById("soil").value;

    try {
        const response = await fetch("https://crop-recommendations-api.onrender.com/api/recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ city, soil })
        });

        if (!response.ok) throw new Error("Failed to fetch recommendations.");

        const data = await response.json();

        document.getElementById("result-city").innerText = data.city;
        document.getElementById("temp").innerText = data.temp;
        document.getElementById("humidity").innerText = data.humidity;
        document.getElementById("rainfall").innerText = data.rainfall;
        document.getElementById("avg-rainfall").innerText = data.avg_rainfall;
        document.getElementById("recommended-crops").innerHTML =
            data.recommended.map(crop => `<li>${crop}</li>`).join("");
        document.getElementById("alternative-crops").innerHTML =
            data.alternative.map(crop => `<li>${crop}</li>`).join("");
        document.getElementById("water-tip").innerText = data.water_tip;
        document.getElementById("climate-tip").innerText = data.climate_tip;

        document.getElementById("results").style.display = "block";
    } catch (error) {
        console.error("Error fetching data:", error);
        alert("Error fetching recommendations. Please try again.");
    } finally {
        document.getElementById("loading").style.display = "none";  // Hide loading
    }
});
