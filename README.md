# SE Project 2025 — Bit Packing Compression (Python)

**Author:** Aya Haddoun — Master 1 in Artificial Intelligence (IA)

---

## 🧭 What is this project about?

This project was developed as part of the **Software Engineering course (M1 AI)**.  
It focuses on implementing a data compression method called **Bit-Packing**, which reduces the memory space used to store integer values by encoding them with the minimum number of bits necessary.

The objective was to explore how **software optimization** and **low-level data representation** can speed up data transmission and improve performance — concepts that are important for AI systems that process large datasets.

---

## 💡 Main Idea

Normally, integers are stored using 32 or 64 bits even when they could fit in fewer bits.  
For instance, numbers between 0 and 100 need only 7 bits — not 32.  

**Bit-Packing** solves this by packing several integers together into a continuous binary stream, using only the number of bits required for each value.  
This reduces memory use and improves data transfer efficiency.

---

## ⚙️ How it works

Two compression strategies were implemented:

- **Non-Crossing Mode:**  
  Each value is stored inside a single 32-bit word. This method is simple and fast.

- **Crossing Mode:**  
  Values can continue over 32-bit boundaries, leading to better space optimization but slightly slower access.

An **overflow area** is used to handle very large numbers that don’t fit within the chosen bit width.  
A **flag and index** are added to indicate these exceptional values.

The implementation follows a clean modular design using a **Factory Pattern** to easily switch between modes.

---

## 🧪 How to use the program

### 1/ Clone this project
```bash
git clone https://github.com/Aya0507/SE-Project-2025.git
cd SE-Project-2025
(Optional) Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

### 2/ Run the main script
python src/main.py


This will launch the benchmark tests and display results such as:

Compression ratio

Compression/decompression time

Latency thresholds for 1, 10, and 100 Mbps

Example output:

crossing  : ratio=1.031, comp=0.10226s, decomp=0.07163s, get=4.08317s
bw=1Mbps  => latency threshold=0.14025s
bw=10Mbps => latency threshold=0.12225s
bw=100Mbps => latency threshold=0.12045s
CSV saved.


A CSV file containing all benchmark results will also be generated automatically.

### Project Structure
SE-Project-2025/
 ├── src/
 │   ├── bitpacking.py   → main compression and decompression logic
 │   ├── benchmark.py    → performance measurement and CSV export
 │   ├── factory.py      → factory design pattern for compressor selection
 │   ├── main.py         → entry point to run the benchmarks
 │   └── __init__.py
 ├── .gitignore
 ├── README.md
 └── output_benchmark_XXXX.csv

### Results and Insights

Crossing mode gives better compression but is slightly slower.

Non-crossing mode is faster for direct data access.

Compression becomes most beneficial when bandwidth is limited (e.g., 1 Mbps).

This project highlights the trade-off between space efficiency and processing speed, a key concept in software engineering and data processing for AI systems.

### What I learned

Developing this project allowed me to practice clean coding, modular design, and GitHub version control.
I also learned how small design decisions at the software level can influence the performance of data-intensive AI applications.

### License

This project was carried out as part of the Software Engineering Project (M1 Artificial Intelligence, 2025).
2025 Aya Haddoun — All rights reserved.

## Project Report
The complete report is available here:  
[Download the PDF](./SE_Project_2025_Report_Aya_Haddoun.pdf)
