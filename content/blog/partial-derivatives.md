+++
draft = false
title = "What are partial derivatives?"
slug = "partial-derivatives"
date = 2021-09-05
[taxonomies]
tags = ["math"]
[extra]
summary = "Understanding how to calculate partial derivatives is fondamental to understand the maths behind machine learning algorithms."
+++


Understanding how to calculate partial derivatives is an important prerequisite for understanding the math used by machine learning algorithms.

Partial derivatives came from the need to understand how a small change in the input of one variable affects the ouput in a function with **several** variables.

Here is what it looks like formalized:

Let's consider $f(x,y)=x^2y+sin(y)$.

The equation below can be read as: "how does a small change in $x$ affect the output of $f(x,y)?$"

$$\frac{\partial f(x,y)}{\partial x}$$

To answer this question, we have to calculate the partial derivative with respect to $x$ while treating $y$ as a constant.

### Calculate the partial derivative of a function

As said in the last paragraph, to differentiate with respect to $x$, we simply threat $y$ as a constant (in our example).

> Whith $u$ a differentiable function and $k$ a constant, we know that:
>
> $$(ku)' = k(u')\quad and \quad k'=0$$

So that:

$$
\begin{aligned}
   \frac{\partial f(x,y)}{\partial x}(x,y)&=\frac{\partial}{\partial x}(x^2\htmlStyle{color: red;}{y}+sin(\htmlStyle{color: red;}{y})) \\\\
   &=2x\htmlStyle{color: red;}{y}
\end{aligned}
$$
Since $sin(y)$ is threated like a constant, it is nulled out.

And for the partial derivative of $f(...)$ whith respect to $y$ we simply threat $x$ as a constant this time:
$$
\begin{aligned}
   \frac{\partial f(x,y)}{\partial y}(x,y)&=\frac{\partial}{\partial y}(\htmlStyle{color: red;}{x^2}y+sin(y)) \\\\
   &=\htmlStyle{color: red;}{x^2}+cos(y)
\end{aligned}
$$

### Derivatives at one point

With these generic functions it is now easy to get the derivative value at a certain point by replacing $x$ and $y$ with the corresponding values.


### afterword

This article should be updated in the future with an intuitive explanation about derivatives. For the moment I assume that the reader has the necessary mathematical knowledge to understand the notation and the words used.