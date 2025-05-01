#!/bin/bash

# Create a local Kubernetes cluster using k3d
k3d cluster create dev-cluster

# If previous command fails (cluster already exists)
# it won't automatically switch the context, so we do it here
kubectl config use-context k3d-dev-cluster

# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD server to be available
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Expose ArgoCD server
kubectl port-forward svc/argocd-server -n argocd 8080:443

# argocd admin initial-password -n argocd | argocd login <ARGOCD_SERVER>

argocd cluster add k3d-dev-cluster