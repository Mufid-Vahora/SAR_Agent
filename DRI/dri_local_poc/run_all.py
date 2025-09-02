
# Convenience runner for the PoC
import subprocess, sys, os, time

def run(cmd):
    print("\n==>", ' '.join(cmd))
    p = subprocess.run(cmd)
    if p.returncode != 0:
        sys.exit(p.returncode)

def main():
    # Assume Docker/Neo4j already up and ollama running
    run([sys.executable, 'neo4j_loader.py', '--csv-root', '../dri_synthetic_data'])
    run([sys.executable, 'gnn_train.py', '--epochs', '5'])
    run([sys.executable, 'detect_and_explain.py', '--topk', '5'])
    print("\n[OK] Pipeline complete. Now run: streamlit run streamlit_app.py\n")

if __name__ == '__main__':
    main()
