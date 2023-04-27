+++
draft = true
title = "A few notes on asymptotic complexity and big-O notation"
date = 2021-10-09
[taxonomies]
tags = ["cs", "math"]
[extra]
summary = "Exploring Big-O notation, which is a central part to every CS major algorithm class."
+++

For the moment it is assumed that the reader knows what the asymptotic complexity is. An update will follow which will introduce the concepts of algorithm runtime and asymptotic complexity. 

This blog post contains solutions to various exercices I had to solve during my computer science master's degree. There are two types of exercices. First, extracting from a simple equation, an asymptotic complexity. Second, solving equations in the form $T(n)=aT({n \over b})+f(n)$ .

## Simple equations

For the following equations, please note that $log(n)=log_2(n)$ .
$$\begin{align}
    T_1(n)= & \sqrt[3]{n^2}+{2n \over 3} \\\\
    T_2(n)= & {n^{1\over 2}+2n^4-4n^2} \over 4+3n    \\\\
    T_3(n)= & \sum_{p=0}^n(n-p) \\\\
    T_4(n)= & log(n^3)+log(\frac{3}{n}) \\\\
    T_5(n)= & n.log(n) + n^{3\over 4}.\sqrt{n} \\\\
    T_6(n)= & \sqrt{n} + {n\over log(n)} \\\\
    T_7(n)= & \sqrt{2n}.log(n)^2+n.log(n) \\\\
    T_8(n)= & 2^{n-32}+n^{64} \\\\
    T_9(n)= & 2^{log(n)}+n^{1\over 3} \\\\
\end{align}$$

Let's try to find the asymptotic complexity associate to these equations.


### 1) $T_1(n)= \sqrt[3]{n^2}+{2n \over 3}$
We observe that $\sqrt[3]{n^2}\in o(n)$, which means that $\sqrt[3]{n^2}$ grows smaller than $n$.

The ratio between $\sqrt[3]{n^2}$ and $n$ decreases when $n$ increases. It can be mathematically written as $\lim\limits_{n\to+\infin} {\sqrt[3]{n^2} \over n}=0$ .

If we draw the graph of the functions that we are comparing, we get the following graph, with $f1(n) = n$ and $f2(n) = \sqrt[3]{n^2}$ .

<svg class="xy-chart"></svg>
<script src="https://cdn.jsdelivr.net/npm/chart.xkcd@1/dist/chart.xkcd.min.js"></script>
<script>
    // func: takes range + f and applies f to range
    // f: simple math func
    function apply(f, start, end) {
        let arr = []
        for (let i = start; i <= end; i++) {
            arr.push(f(i))       
        }
        return arr
    }
    function gen_labels(start, end) {
        let arr = []
        for (let i = start; i <= end; i++) {
            arr.push(`${i}`)       
        }
        return arr
    }
    let svg = document.querySelector('.xy-chart')
    let lineChart = new chartXkcd.Line(svg, {
        title: 'comparing f1(n) & f2(n)',
        xLabel: 'n',
        yLabel: 'y',
        data: {
            labels: gen_labels(1, 10),
            datasets: [
                {
                    label: 'f1(n)',
                    data: apply(x => x, 1, 10),
                }, 
                {
                    label: 'f2(n)',
                    data: apply(x => Math.pow(x*x, 1/3), 1, 10),
                }
            ],
        },
        options: {
            yTickCount: 10,
            legendPosition: chartXkcd.config.positionType.upLeft,
            backgroundColor: '#f6f6f6'
        }
    })
</script>

As one can clearly see, one function is dominated by the other for each value of $n$ bigger than 1.

<br><br>

### 2) $T_2(n)= {{n^{1\over 2}+2n^4-4n^2} \over 4+3n}$

To get the corresponding asymptotic complexity of this example, we first need to divide each term by $n$ .

This gives us the following equation:
$${{\frac{\sqrt n}{n} + \frac{2n^4}{n} - \frac{4n^2}{n}} \over \frac{4}{n} + \frac{3n}{n}}$$
Divide by $n$ to get:
$${{\frac{\sqrt n}{n} + 2n^3 - 4n} \over \frac{4}{n} + 3}$$


We clearly see that the leading term in this reduce equation is $n^3$ . So we can infer that $\frac{\sqrt n}{n}\in o(1)\in o(n^3)$ and $n\in o(n^3)$ .

So the solution to $T_2$ is $T_2 \in \theta(n^3)$.

Like before, we can visualize the two functions to show which one dominates the other. Here $f1(n)=n^3$ and $f2(n)=n$

Let's visualize $f1$ and $f2$ :


<svg class="T2-chart"></svg>
<script>
    svg = document.querySelector('.T2-chart')
    lineChart = new chartXkcd.Line(svg, {
        title: 'comparing f1(n) & f2(n)',
        xLabel: 'n',
        yLabel: 'y',
        data: {
            labels: gen_labels(1, 10),
            datasets: [
                {
                    label: 'f1(n)',
                    data: apply(x => x*x*x*x, 1, 10),
                }, 
                {
                    label: 'f2(n)',
                    data: apply(x => x, 1, 10),
                }
            ],
        },
        options: {
            yTickCount: 10,
            legendPosition: chartXkcd.config.positionType.upLeft,
            backgroundColor: '#f6f6f6'
        }
    })
</script>

As expected, $f1$ clearly dominates $f2$, and thus is the upper-bound (here an asymptotically tight-bound for $T_2$).