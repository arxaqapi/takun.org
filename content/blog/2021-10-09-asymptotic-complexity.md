+++
draft = true
title = "A few notes on asymptotic complexity and big-O notation"
date = 2021-10-09
[taxonomies]
tags = ["cs", "math"]
[extra]
summary = "What is the so called big-O notation that is central to every class on algorithms?"
+++
<!-- slug = "partial-derivatives" -->

This blog post contains solutions to various exercices I had to solve during my computer science master's degree. There are two types of exercices. First, extracting from a simple equation, an asymptotic complexity. Second, solving equations in the form $T(n)=aT({n \over b})+f(n)$.

## Simple equations

For the following equations, please note that $log(n)=log_2(n)$.
$$
\begin{align}
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

