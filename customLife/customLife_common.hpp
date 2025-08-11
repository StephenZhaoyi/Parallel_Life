#pragma once
#include <iostream>
#include <vector>
#include <string>
#include <cstdint>
#include <array>

using Grid = std::vector<std::vector<uint8_t>>;
extern int gWidth;
extern int gHeight;

struct RuleTables {
    std::array<uint8_t,9> B{}; 
    std::array<uint8_t,9> S{}; 
};

inline RuleTables parse_rulestring(const std::string& rule) {
    // Accept forms like: B3/S23 or lower-case b3/s23
    RuleTables t;
    std::string r;
    r.reserve(rule.size());
    for (char c : rule) {
        if (c!=' ' && c!=',') r.push_back(c);
    }
    auto posB = r.find_first_of("Bb");
    auto posS = r.find_first_of("Ss");
    if (posB == std::string::npos && posS == std::string::npos) {
        // default Conway Life
        t.B.fill(0); t.S.fill(0);
        t.B[3] = 1; t.S[2] = 1; t.S[3] = 1;
        return t;
    }
    t.B.fill(0); t.S.fill(0);

    bool invalidFound = false;
    std::string invalidChars; // collect any invalid digit characters
    auto fillDigits = [&invalidFound, &invalidChars](const std::string& s, size_t from, std::array<uint8_t,9>& arr) {
        for (size_t i = from; i < s.size(); ++i) {
            char c = s[i];
            if (c=='/' || c=='B' || c=='b' || c=='S' || c=='s') break;
            if (c >= '0' && c <= '8') {
                arr[c - '0'] = 1;
            } else if (c >= '0' && c <= '9') {
                invalidFound = true;
                if (invalidChars.find(c) == std::string::npos) invalidChars.push_back(c);
            } else if (std::isdigit(static_cast<unsigned char>(c))) { // any other digit (future-proof)
                invalidFound = true;
                if (invalidChars.find(c) == std::string::npos) invalidChars.push_back(c);
            }
        }
    };

    if (posB != std::string::npos) fillDigits(r, posB + 1, t.B);
    if (posS != std::string::npos) fillDigits(r, posS + 1, t.S);

    if (invalidFound) {
        std::cerr << "Warning: digits >8 ignored in rulestring: ";
        for (size_t i = 0; i < invalidChars.size(); ++i) {
            if (i) std::cerr << ',';
            std::cerr << invalidChars[i];
        }
        std::cerr << std::endl;
    }
    return t;
}

inline int neighbor_count(const Grid& g, int y, int x) {
    int cnt = 0;
    for (int dy = -1; dy <= 1; ++dy) {
        for (int dx = -1; dx <= 1; ++dx) {
            if (dy || dx)
                cnt += g[(y + dy + gHeight) % gHeight][(x + dx + gWidth) % gWidth];
        }
    }
    return cnt;
}
