FROM python:latest
WORKDIR /workdir

# System dependencies
RUN apt update && apt upgrade --yes && apt install --yes \
    curl \
    jq

# Install elan (Lean version manager)
RUN curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh -s -- -y

# Install Lean toolchain required by qed
RUN . "$HOME/.elan/env" && elan toolchain install leanprover/lean4:v4.28.0

# Clone and build qed from source
RUN git clone https://github.com/tskovlund/qed.git /opt/qed
RUN . "$HOME/.elan/env" && cd /opt/qed && lake build

# Add qed to PATH
RUN ln -sf /opt/qed/.lake/build/bin/qed /usr/local/bin/qed

# Copy source and install Python dependencies
COPY . .
RUN pip install --upgrade pip && pip install \
    black \
    flake8 \
    mutmut \
    mypy \
    pylint \
    pytest \
    pytest-cov \
    typer[all]

RUN make install
