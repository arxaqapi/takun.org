+++
draft = true
title = "Dynamic programming"
date = 2021-10-11
[taxonomies]
tags = ["cs", "algorithms"]
[extra]
summary = "Introducing... Dynamic programming"
+++


Before I loose you whith an attempt to explain what dynamic programming is, we will directly jump into some well known examples.


## Fibonacci numbers

The fibonacci suite of numbers is a really well know suite. It's definition is elegant and allows to introduce concepts like recursion for beginners.

A little remainderr on how to compute the $n^{th}$ term of the fibonacci sequence.

$$F(n) = F(n-1) + F(n - 2)$$

### Naïve solution

The implementation is straightfoward in any programming language.

```ocaml
let rec f n = match n with
    | 0 -> 0
    | 1 -> 1
    | x -> f (x - 1) + f (x - 2)
```

Beautiful, isn't it?

Well not really, the runtime complexity of this algorithm is horrible. For each call of $F$ we do two additional calls most of the time. This gives the horrendus looking asymptotic complexity of $O(2^n)$ .

If we dissect the execution of our algorithm for $n=4$ we have the following calls being made.

- For $F(4)$, call $F(3) + F(2)$.
    - For $F(3)$, call $F(2) + F(1)$, simplified to $F(2) + 1$ .
      - For $\color{green}F(2)$, call $F(1) + F(0)$, which returns $1 + 0$ .
    - $F(3)$ now returns $1 + 1$ .
    - For $\color{green}F(2)$, call $F(1) + F(0)$ which returns $1 + 0$ .
- $F(4) = 2 + 1 = 3$ 

As one can clearly see, $F(2)$ is being computed two times (highlighted in green). And this is only for a small value, as said before, the complexity of the naïve recusive approach is $O(2^n)$.

But since there are redundant calls being made, a simple solution would be to store the intermediate results, no?

Yes and this is exactly what dynamic programming is all about.


### Introducing memoization
Each time we call $F(n)$, we simply check if the value has already been computed. The nature of the problem allows us to store the intermediate values in a simple array.

```ocaml
let f_memo n = 
  let memo = Array.make (n + 1) 0 in
  let rec term n = match n with
      | 0 -> 0
      | 1 -> 1
      | x ->
        if memo.(x) = 0 
        then 
          memo.(x) <- (term (n - 1)) + (term (n - 2));
        memo.(x)
  in term n
```
The code looks a little bit complicated, but it is, in fact, really simple.

What is going on is that we first create an array of size $n+1$ which will hold all the intermediate values of our computation and thus allowing us to remove all duplicate recursive calls.

We simpy check if the wanted value has already been computed, if this is the case, we simply return the value contained in our **memoization** structure (here a simple array).

For the moment, the techniques used can be called top-down. We start from $n$ and go down until we reach our base cases. If we draw the corresponding call tree, we clearly see why we call it top-down.

Another approach could be to simply start from the bottom, the small values, and go up to n.

Down below is a simple iterative solution doing exactly that. 

```ocaml
let fibo_dp n = 
  let t = Array.make (n + 1) 0 in
  t.(0) <- 0;
  t.(1) <- 1;
  for i = 2 to n do
    t.(i) <- t.(i - 1) + t.(i - 2)
  done;
  t.(n)
```

Whith all these beautiful improvements done, our complexity to compute the $n^{th}$ fibonacci number is now $\theta(n)$. 

