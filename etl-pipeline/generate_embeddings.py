import os
import json

import numpy as np
from tqdm import tqdm

from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.models import KeyedVectors
from gensim.scripts.glove2word2vec import glove2word2vec
from sentence_transformers import SentenceTransformer
from InstructorEmbedding import INSTRUCTOR

from typing import Literal
from utils.get_top_level_dirs import get_top_level_dirs

EmbeddingModelNameType = Literal[
    "sbert", "instructor", "mxbai", "sfr-mistral", "word2vec", "doc2vec", "glove"
]


class Glove:
    def __init__(self, size=Literal[50, 100, 200, 300], aggregation="mean"):
        self.size = size
        self.aggregation = aggregation

        print("Loading Glove model...")

        self.vectors = KeyedVectors.load_word2vec_format(
            f"./model_data/glove_6b_vectors/glove.6B.{size}d.txt",
            binary=False,
            no_header=True,
        )

        print("Glove model loaded successfully!")

    def encode(self, text: list[str], normalize_embeddings=True):
        """
        Embedding normalization is not currently implemented.
        """
        text = text[0]

        vec = np.zeros(self.size).reshape(
            (1, self.size)
        )  # create for size of glove embedding and assign all values 0
        count = 0
        for word in text.split():
            # print("\n word:   ", word)
            try:
                # print("golve vect", self.vectors[word])
                vec += self.vectors[word].reshape(
                    (1, self.size)
                )  # update vector with new word
                count += 1  # counts every word in sentence
            except KeyError:
                continue
        if self.aggregation == "mean":
            if count != 0:
                vec /= count  # get average of vector to create embedding for sentence
            return vec
        elif self.aggregation == "sum":
            return vec


def generate_doc2vec_embeddings(is_regenerate_embeddings: bool):
    """
    Currently doc2vec is the only model which requires training on all data before generating embeddings.
    """
    for uni_dir in get_top_level_dirs("./data"):
        uni_subjects_dir = f"./data/{uni_dir}"
        embeddings_dir = f"{uni_subjects_dir}/subjects/embeddings/doc2vec"
        os.makedirs(embeddings_dir, exist_ok=True)

        existing_embeddings = set(
            [name.replace(".json", "") for name in os.listdir(embeddings_dir)]
        )
        document_names = (
            set(
                [
                    name.replace(".txt", "")
                    for name in os.listdir(f"{uni_subjects_dir}/subjects/text")
                ]
            )
            - existing_embeddings
        )

        if len(document_names) == 0:
            print(f"All doc2vec embeddings for {uni_dir} already exist. Skipping...")
            continue

        documents = []

        for document_name in tqdm(document_names, desc="tagging documents"):
            with open(
                f"{uni_subjects_dir}/subjects/text/{document_name}.txt", "r"
            ) as f:
                document = f.read().lower()
                documents.append(TaggedDocument(document, [document_name]))

        # Initialize the Doc2Vec model
        model = Doc2Vec(
            vector_size=384,  # Dimensionality of the document vectors
            window=9,  # Maximum distance between the current and predicted word within a sentence
            min_count=1,  # Ignores all words with total frequency lower than this
            workers=4,  # Number of CPU cores to use for training
            epochs=20,
        )  # Number of training epochs

        # Build the vocabulary
        model.build_vocab(documents)

        # Train the model
        print("Training the model...")
        model.train(documents, total_examples=model.corpus_count, epochs=model.epochs)

        for document_name in tqdm(document_names, desc="generating embeddings"):
            if is_regenerate_embeddings or document_name not in existing_embeddings:
                embedding = model.dv[document_name].tolist()

                with open(
                    f"{embeddings_dir}/{document_name}.json",
                    "w",
                ) as f:
                    json.dump(embedding, f)


def generate_embedding_per_document(
    model,
    modelType: Literal["sbert", "instructor", "glove"],
    is_regenerate_embeddings: bool,
):
    for uni_dir in get_top_level_dirs("./data"):
        uni_subjects_dir = f"./data/{uni_dir}"
        embeddings_dir = f"{uni_subjects_dir}/subjects/embeddings/{modelType}"
        os.makedirs(embeddings_dir, exist_ok=True)

        existing_embeddings = set(os.listdir(embeddings_dir))

        for subject_text_filename in tqdm(
            os.listdir(f"{uni_subjects_dir}/subjects/text"), desc=uni_dir
        ):
            subject_code = subject_text_filename.split(".")[0]
            subject_embedding_filename = f"{subject_code}.json"

            if (
                is_regenerate_embeddings
                or subject_embedding_filename not in existing_embeddings
            ):
                with open(
                    f"{uni_subjects_dir}/subjects/text/{subject_text_filename}", "r"
                ) as f:
                    subject_text = f.read()

                embedding = model.encode(
                    [subject_text], normalize_embeddings=True
                ).tolist()[0]

                with open(
                    f"{embeddings_dir}/{subject_embedding_filename}",
                    "w",
                ) as f:
                    json.dump(embedding, f)


def generate_embeddings(
    modelTypes: list[EmbeddingModelNameType], is_regenerate_embeddings: bool = True
):
    for modelType in set(modelTypes):
        print(f"Generating {modelType} embeddings...")

        model = None

        if modelType == "sbert":
            model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
            generate_embedding_per_document(model, modelType, is_regenerate_embeddings)
        elif modelType == "mxbai":
            model = SentenceTransformer("mixedbread-ai/mxbai-embed-large-v1")
            generate_embedding_per_document(model, modelType, is_regenerate_embeddings)
        elif modelType == "sfr-mistral":
            model = SentenceTransformer("Salesforce/SFR-Embedding-Mistral")
            generate_embedding_per_document(model, modelType, is_regenerate_embeddings)
        elif modelType == "instructor":
            model = INSTRUCTOR("hkunlp/instructor-xl")
            generate_embedding_per_document(model, modelType, is_regenerate_embeddings)
        elif modelType == "doc2vec":
            generate_doc2vec_embeddings(is_regenerate_embeddings)
        elif modelType == "glove":
            model = Glove(300, aggregation="mean")
            generate_embedding_per_document(model, modelType, is_regenerate_embeddings)
        else:
            print("Invalid model type. Skipping this model type.")
            continue

        print(f"{modelType} embeddings generated successfully!")
