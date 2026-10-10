// CASPER: maximum-priority greedy matching and constrained local refinement.
// Input is numeric only. Python handles survey preprocessing and explanations.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <queue>
#include <stdexcept>
#include <utility>
#include <vector>

struct Edge {
    int u, v;
    double w;
    bool operator<(const Edge& other) const {
        if (w != other.w) return w < other.w;
        if (u != other.u) return u > other.u;
        return v > other.v;
    }
};

void print_pairs(const std::vector<std::pair<int,int>>& pairs) {
    std::cout << '[';
    for (std::size_t i=0; i<pairs.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << '[' << pairs[i].first << ',' << pairs[i].second << ']';
    }
    std::cout << ']';
}

int main() {
    try {
        int n, m, sweeps, fair;
        if (!(std::cin >> n >> m >> sweeps >> fair) || n<0 || n>1000 || m<0 || m>n*(n-1)/2 || sweeps<0 || sweeps>50 || (fair!=0 && fair!=1))
            throw std::runtime_error("Invalid engine header");
        const auto start=std::chrono::steady_clock::now();
        const double absent=-std::numeric_limits<double>::infinity();
        std::vector<std::vector<double>> w(n,std::vector<double>(n,absent));
        std::priority_queue<Edge> heap;
        for (int i=0; i<m; ++i) {
            Edge e;
            if (!(std::cin>>e.u>>e.v>>e.w) || e.u<0 || e.v<0 || e.u>=n || e.v>=n || e.u==e.v || !std::isfinite(e.w))
                throw std::runtime_error("Invalid edge");
            if (e.u>e.v) std::swap(e.u,e.v);
            if (std::isfinite(w[e.u][e.v])) throw std::runtime_error("Duplicate edge");
            w[e.u][e.v]=w[e.v][e.u]=e.w;
            heap.push(e);
        }
        std::vector<bool> used(n,false);
        std::vector<std::pair<int,int>> pairs;
        while (!heap.empty()) {
            Edge e=heap.top(); heap.pop();
            if (!used[e.u] && !used[e.v]) {
                used[e.u]=used[e.v]=true; pairs.emplace_back(e.u,e.v);
            }
        }
        const auto initial=pairs;
        double total=0, squares=0;
        for (auto [a,b]:pairs) {total+=w[a][b];squares+=w[a][b]*w[a][b];}
        const int k=static_cast<int>(pairs.size());
        auto variance=[k](double sum,double sq){return k?std::max(0.0,sq/k-(sum/k)*(sum/k)):0.0;};
        const auto greedy_end=std::chrono::steady_clock::now();
        int swaps=0, passes=0;
        bool converged=sweeps>0;
        constexpr double eps=1e-10;
        for (int pass=0;pass<sweeps;++pass) {
            bool improved=false; ++passes;
            for(int i=0;i<k;++i) for(int j=i+1;j<k;++j) {
                auto [a,b]=pairs[i];auto [c,d]=pairs[j];
                const double old1=w[a][b],old2=w[c][d];
                const std::pair<int,int> candidates[2][2]={{{a,c},{b,d}},{{a,d},{b,c}}};
                int best=-1;double best_total=total, best_variance=variance(total,squares),best_floor=std::min(old1,old2);
                for(int option=0;option<2;++option) {
                    auto [u,v]=candidates[option][0];auto [x,y]=candidates[option][1];
                    if(!std::isfinite(w[u][v])||!std::isfinite(w[x][y]))continue;
                    const double v1=w[u][v],v2=w[x][y];
                    const double next_total=total-old1-old2+v1+v2;
                    const double next_sq=squares-old1*old1-old2*old2+v1*v1+v2*v2;
                    const double next_var=variance(next_total,next_sq), floor=std::min(v1,v2);
                    bool accept;
                    if(fair) {
                        accept=next_total>=total-eps && floor>=std::min(old1,old2)-eps && next_var<=variance(total,squares)+eps
                               && (next_total>total+eps||floor>std::min(old1,old2)+eps||next_var<variance(total,squares)-eps);
                    } else accept=next_total>total+eps;
                    if(accept && (best==-1||next_total>best_total+eps||
                        (std::abs(next_total-best_total)<=eps && (floor>best_floor+eps||next_var<best_variance-eps)))) {
                        best=option;best_total=next_total;best_variance=next_var;best_floor=floor;
                    }
                }
                if(best!=-1) {
                    pairs[i]=candidates[best][0];pairs[j]=candidates[best][1];
                    double v1=w[pairs[i].first][pairs[i].second],v2=w[pairs[j].first][pairs[j].second];
                    total+=v1+v2-old1-old2;squares+=v1*v1+v2*v2-old1*old1-old2*old2;
                    ++swaps;improved=true;
                }
            }
            if(!improved)break;
            if(pass==sweeps-1)converged=false;
        }
        const auto finish=std::chrono::steady_clock::now();
        auto ms=[](auto a,auto b){return std::chrono::duration<double,std::milli>(b-a).count();};
        std::cout<<std::setprecision(12)<<"{\"pairs\":";print_pairs(pairs);
        std::cout<<",\"greedy_pairs\":";print_pairs(initial);
        std::cout<<",\"swaps\":"<<swaps<<",\"passes\":"<<passes
                 <<",\"converged\":"<<(converged?"true":"false")
                 <<",\"greedy_ms\":"<<ms(start,greedy_end)
                 <<",\"refinement_ms\":"<<ms(greedy_end,finish)<<"}\n";
        return 0;
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
