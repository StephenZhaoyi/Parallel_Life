#include <iostream>
#include <vector>
#include <random>
#include <chrono>
#include <thread>

using Grid = std::vector<std::vector<uint8_t>>;

constexpr int kWidth  = 80;   // 终端列数
constexpr int kHeight = 24;   // 终端行数
constexpr int kFPS    = 10;   // 帧率（代 / 秒）

// 统计 (y,x) 周围 8 邻居活细胞个数，带环绕边界
inline int neighbor_count(const Grid& g, int y, int x) {
    int cnt = 0;
    for (int dy = -1; dy <= 1; ++dy)
        for (int dx = -1; dx <= 1; ++dx)
            if (dy || dx)
                cnt += g[(y + dy + kHeight) % kHeight][(x + dx + kWidth) % kWidth];
    return cnt;
    
}

// 计算下一代
void step(Grid& cur, Grid& nxt) {
    for (int y = 0; y < kHeight; ++y)
        for (int x = 0; x < kWidth; ++x) {
            int n = neighbor_count(cur, y, x);
            nxt[y][x] = (n == 3) || (cur[y][x] && n == 2);
        }
    cur.swap(nxt);                 // 交换双缓冲
}

// 随机初始化（活细胞比例 p）
void random_init(Grid& g, double p = 0.25) {
    std::mt19937 rng{std::random_device{}()};
    std::bernoulli_distribution bern(p);
    for (auto& row : g)
        for (auto& cell : row)
            cell = bern(rng);
}

// 手动初始化（用户输入活细胞坐标，输入负数结束）
void manual_init(Grid& g) {
    g[10][40] = 1; // 预设一个活细胞
    g[10][41] = 1;
    g[10][42] = 1;
}

// 在屏幕 (row,col) 输出字符（0-based）
inline void put_at(int row, int col, char c) {
    std::cout << "\033[" << row + 1 << ';' << col + 1 << 'H' << c;
}

// 绘制网格到终端
void draw(const Grid& g) {
    std::cout << "\033[H";         // 光标回到左上
    for (int y = 0; y < kHeight; ++y) {
        for (int x = 0; x < kWidth; ++x)
            std::cout << (g[y][x] ? '#' : ' ');
        std::cout << '\n';
    }
    std::cout.flush();
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cout << "\033[2J";        // 清屏

    Grid cur(kHeight, std::vector<uint8_t>(kWidth, 0));
    Grid nxt = cur;

    manual_init(cur);  // 手动初始化活细胞

    const auto frame_interval = std::chrono::milliseconds(1000 / kFPS);
    while (true) {
        auto frame_start = std::chrono::steady_clock::now();

        draw(cur);
        step(cur, nxt);

        std::this_thread::sleep_until(frame_start + frame_interval);
    }
    return 0;
}
