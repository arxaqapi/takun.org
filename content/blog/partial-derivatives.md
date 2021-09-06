+++
draft = true
title = "What are partial derivatives?"
slug = "partial-derivatives"
date = 2021-09-05
[taxonomies]
tags = ["math"]
[extra]
summary = "Understanding how to calculate partial derivatives is fondamental to understand the maths behind machine learning algorithms."
+++

Understanding how to calculate partial derivatives is fondamental to understanding the maths behind machine learning optimisation algorithms.

Partial derivatives came from the need to understand how a small change in the input of one variable affects the ouput in a function with several variables.

Here is what it looks like formalized:

Let's take $f(x,y)=x^2y+sin(y)$

The equation below can be read as: "how does a change in $x$ affect the output of $f(x,y)?$"

$$\frac{\partial f(x,y)}{\partial x}$$

To answer this question, we have to calculate the partial derivative with respect to $x$.

## The calculation
To do this we simply differentiate with respect to $x$ but with threating $y$ as a constant.

> We know that $(ku)' = k(u')$ with $u$ being a differentiable function and that $k'= 0$

So that:

$$
\begin{aligned}
   \frac{\partial f(x,y)}{\partial x}(x,y)&=\frac{\partial}{\partial x}(x^2\htmlStyle{color: red;}{y}+sin(\htmlStyle{color: red;}{y})) \\\\
   &=2x\htmlStyle{color: red;}{y}
\end{aligned}
$$
Since $sin(y)$ is threated like a constant, it is nulled out.

And for the partial derivative in respect to $y$ we simply threat $x$ as a constant this time:
$$
\begin{aligned}
   \frac{\partial f(x,y)}{\partial y}(x,y)&=\frac{\partial}{\partial y}(\htmlStyle{color: red;}{x^2}y+sin(y)) \\\\
   &=\htmlStyle{color: red;}{x^2}+cos(y)
\end{aligned}
$$

### Derivatives at one point

With these generic functions it is now easy to get the derivative value at a certain point.
