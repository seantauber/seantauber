# 🚀 Awesome GenAI, AI, and Data Science Resources

Welcome to my curated list of cutting-edge and interesting repositories in the fields of Generative AI, Artificial Intelligence, and Data Science. As a technical product manager specializing in these areas, I've compiled this list to help developers, researchers, and enthusiasts stay up-to-date with the latest advancements and tools.

## 📚 Table of Contents

- [Generative AI](#generative-ai)
- [Artificial Intelligence](#artificial-intelligence)
- [Data Science](#data-science)
- [MLOps & AI Infrastructure](#mlops--ai-infrastructure)
- [AI Ethics & Responsible AI](#ai-ethics--responsible-ai)
- [How This Landing Page Works](#how-this-landing-page-works)

## Generative AI

### Large Language Models (LLMs)
- [🤗 Hugging Face Transformers](https://github.com/huggingface/transformers) - State-of-the-art Natural Language Processing for PyTorch and TensorFlow 2.0.
- [OpenAI GPT-3](https://github.com/openai/gpt-3) - Language Models are Few-Shot Learners.
- [Google BERT](https://github.com/google-research/bert) - TensorFlow code and pre-trained models for BERT.

### Image Generation
- [DALL-E](https://github.com/openai/DALL-E) - PyTorch package for the discrete VAE used for DALL·E.
- [Stable Diffusion](https://github.com/CompVis/stable-diffusion) - A latent text-to-image diffusion model.

### Audio Generation
- [Jukebox](https://github.com/openai/jukebox) - A generative model for music.
- [TTS](https://github.com/coqui-ai/TTS) - Deep learning toolkit for Text-to-Speech, battle-tested in research and production.

## Artificial Intelligence

### Machine Learning Frameworks
- [TensorFlow](https://github.com/tensorflow/tensorflow) - An open source machine learning framework for everyone.
- [PyTorch](https://github.com/pytorch/pytorch) - Tensors and Dynamic neural networks in Python with strong GPU acceleration.

### Reinforcement Learning
- [OpenAI Gym](https://github.com/openai/gym) - A toolkit for developing and comparing reinforcement learning algorithms.
- [Stable Baselines3](https://github.com/DLR-RM/stable-baselines3) - Reliable implementations of reinforcement learning algorithms.

## Data Science

### Data Visualization
- [Plotly](https://github.com/plotly/plotly.py) - The interactive graphing library for Python.
- [Seaborn](https://github.com/mwaskom/seaborn) - Statistical data visualization using matplotlib.

### Data Analysis
- [Pandas](https://github.com/pandas-dev/pandas) - Flexible and powerful data analysis / manipulation library for Python.
- [Scikit-learn](https://github.com/scikit-learn/scikit-learn) - Machine Learning in Python.

## MLOps & AI Infrastructure

- [MLflow](https://github.com/mlflow/mlflow) - Open source platform for the machine learning lifecycle.
- [Kubeflow](https://github.com/kubeflow/kubeflow) - Machine Learning Toolkit for Kubernetes.
- [DVC](https://github.com/iterative/dvc) - Data Version Control | Git for Data & Models | ML Experiments Management.

## AI Ethics & Responsible AI

- [AI Fairness 360](https://github.com/Trusted-AI/AIF360) - Fairness metrics for datasets and machine learning models.
- [Ethical AI](https://github.com/EthicalML/ethical-ai) - A practical guide to building more ethical AI systems.


## How This Landing Page Works

This GitHub landing page is dynamically updated to showcase my latest interests and discoveries in the fields of AI, Machine Learning, and Data Science. Here's how it works:

1. **Automated Updates**: The repository list you see above is automatically updated daily using GitHub Actions.

2. **Starred Repositories**: The content is based on my GitHub starred repositories, reflecting my current interests and valuable finds in the tech world.

3. **AI-Powered Organization**: An AI model (GPT-3.5-turbo) is used to categorize and organize the repositories, ensuring that the list remains well-structured and informative.

4. **Minimal Manual Intervention**: Once set up, this page requires little to no manual updating, keeping the content fresh with minimal effort.

### How to Implement This for Your Own GitHub

If you'd like to create a similar landing page for your GitHub profile:

1. Fork this repository.
2. Set up the following secrets in your forked repository's settings:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `PAT`: A GitHub Personal Access Token with appropriate permissions
3. Update the `update_readme.py` script in the `.github/scripts/` directory:
   - Replace `"YourGitHubUsername"` with your actual GitHub username
4. Customize the README.md template to fit your personal brand and interests.
5. The GitHub Action will run daily, updating your README with your latest starred repositories.

Feel free to modify the script or the README structure to better suit your needs. Happy showcasing!

---

**Note**: This landing page uses OpenAI's GPT-3.5-turbo model. Make sure you comply with OpenAI's use-case policies and monitor your API usage to manage costs.

---

## 🌟 Contributing

Feel free to open a pull request if you have any suggestions for additions or improvements to this list. Let's collaborate to keep this resource up-to-date and valuable for the community!

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

---

📊 *Last updated: [July 25, 2024]*

🔗 Connect with me on [LinkedIn](https://www.linkedin.com/in/taubersean)
