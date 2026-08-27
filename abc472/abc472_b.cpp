#include<bits/stdc++.h>
using namespace std;    
int main() {
    int n;
    cin >> n;
    vector<long long> a;
    for(int i = 0; i < n; i++){
        int x;
        cin >> x;
        a.push_back(x);
    }
    long long length{0};
    for(int i = 0; i < n; i++){
        length += a[i];
    }
    long long part1{0};
    long long ans{LLONG_MAX};
    long long part2{0};
    for(int i = 0; i < n; i++){
        part1 += a[i];
        part2 = length - part1;
        ans = min(ans, abs(part1 - part2));
    }
    cout << ans << endl;
    return 0;
}