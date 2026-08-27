#include <bits/stdc++.h>
using namespace std;

int main() {
    int n, m;
    long long k;

    cin >> n >> m >> k;

    vector<long long> a(n);

    for (int i = 0; i < n; i++) {
        cin >> a[i];
    }

    long long sum = 0;

    for (int i = 0; i < n; i++) {
        if (i - m >= 0) {
            sum -= a[i - m];
        }
        if (sum + a[i] <= k) {
            cout << "Yes\n";
            sum += a[i];
        }
        else {
            cout << "No\n";
            a[i] = 0; 
        }
    }

    return 0;
}