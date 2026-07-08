async function askAnalytics() {

    const question = document.getElementById("question").value.trim();

    if (!question) {
        alert("Please enter a question.");
        return;
    }

    document.getElementById("answer").innerHTML = "⏳ Analyzing...";
    document.getElementById("sql").innerHTML = "...";
    document.getElementById("rows").innerHTML = "...";

    try {

        const response = await fetch("/analytics/ask", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                question: question
            })

        });

        const data = await response.json();

        document.getElementById("answer").innerHTML =
            data.answer || "No answer returned.";

        document.getElementById("sql").innerHTML =
            data.sql_query || "No SQL generated.";

        document.getElementById("rows").innerHTML =
            JSON.stringify(data.rows, null, 2);

    }

    catch (err) {

        document.getElementById("answer").innerHTML =
            "❌ Failed to connect to the Analytics API.";

        document.getElementById("sql").innerHTML = "";

        document.getElementById("rows").innerHTML = "";

        console.error(err);

    }

}
