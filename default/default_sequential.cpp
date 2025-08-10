#include <iostream>
#include <vector>
#include <random>
#include <chrono>
#include <thread>

using Grid = std::vector<std::vector<uint8_t>>;

static int gWidth  = 80;   // terminal columns (runtime configurable)
static int gHeight = 24;   // terminal rows (runtime configurable)
constexpr int kFPS    = 10;   // frames (generations) per second

// Count live neighbors around (y,x) (8 neighbors) with wrap-around
inline int neighbor_count(const Grid& g, int y, int x) {
    int cnt = 0;
    for (int dy = -1; dy <= 1; ++dy)
        for (int dx = -1; dx <= 1; ++dx)
            if (dy || dx)
                // wrap-around indexing
                cnt += g[(y + dy + gHeight) % gHeight][(x + dx + gWidth) % gWidth];
    return cnt;
    
}

// Compute next generation
void step(Grid& cur, Grid& nxt) {
    for (int y = 0; y < gHeight; ++y)
        for (int x = 0; x < gWidth; ++x) {
            int n = neighbor_count(cur, y, x);
            // Apply Conway's rules:
            nxt[y][x] = (n == 3) || (cur[y][x] && n == 2);
        }
    cur.swap(nxt);                 // swap double buffers
}

// Random initialization (live cell probability p)
void random_init(Grid& g, double p = 0.25) {
    std::mt19937 rng{std::random_device{}()};
    std::bernoulli_distribution bern(p);
    for (auto& row : g)
        for (auto& cell : row)
            cell = bern(rng);
}

// Output character at screen position (row,col) (0-based)
inline void put_at(int row, int col, char c) {
    std::cout << "\033[" << row + 1 << ';' << col + 1 << 'H' << c;
}

// Draw grid to terminal
void draw(const Grid& g) {
    std::cout << "\033[H";         // move cursor to top-left
    for (int y = 0; y < gHeight; ++y) {
        for (int x = 0; x < gWidth; ++x)
            std::cout << (g[y][x] ? '#' : ' ');
        std::cout << '\n';
    }
    std::cout.flush();
}

int main(int argc, char* argv[]) {
    std::ios::sync_with_stdio(false);
    bool draw_enabled = true;
    int steps = -1;          // -1 means run forever (interactive mode)
    double prob = 0.25;      // live cell probability

    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        if (a == "--no-draw") draw_enabled = false;
        else if (a == "--steps" && i + 1 < argc) steps = std::stoi(argv[++i]);
        else if (a == "--prob" && i + 1 < argc) prob = std::stod(argv[++i]);
        else if (a == "--width" && i + 1 < argc) gWidth = std::stoi(argv[++i]);
        else if (a == "--height" && i + 1 < argc) gHeight = std::stoi(argv[++i]);
    }

    if (draw_enabled) std::cout << "\033[2J"; // clear screen

    if (gWidth <= 0 || gHeight <= 0) {
        std::cerr << "Invalid dimensions" << std::endl;
        return 1;
    }
    Grid cur(gHeight, std::vector<uint8_t>(gWidth, 0));
    Grid nxt = cur;
    random_init(cur, prob);

    // Benchmark mode (no draw & finite steps): just run and output timing
    if (!draw_enabled && steps > 0) {
        auto t0 = std::chrono::steady_clock::now();
        for (int i = 0; i < steps; ++i) {
            step(cur, nxt);
        }
        auto t1 = std::chrono::steady_clock::now();
        auto ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    std::cout << "steps=" << steps
          << " width=" << gWidth
          << " height=" << gHeight
          << " time_ms=" << ms
          << " per_step_ms=" << ms / steps
          << " per_cell_us=" << (ms * 1000.0) / (steps * gWidth * gHeight)
          << "\n";
        return 0;
    }

    // Interactive animation loop
    const auto frame_interval = std::chrono::milliseconds(1000 / kFPS);
    int iter = 0;
    while (steps < 0 || iter < steps) {
        auto frame_start = std::chrono::steady_clock::now();
        if (draw_enabled) draw(cur);
        step(cur, nxt);
        if (draw_enabled) {
            std::this_thread::sleep_until(frame_start + frame_interval);
        }
        ++iter;
    }
    return 0;
}
