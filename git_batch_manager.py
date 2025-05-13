import asyncio
import os
import subprocess
import uuid
from typing import List, Tuple
import pathlib
from dotenv import load_dotenv
load_dotenv()

GITHUB_USER = os.getenv("GITHUB_USER")
GITHUB_REPO = os.getenv("GITHUB_REPO")
BRANCH = os.getenv("BRANCH")


class GitBatchManager:
    def __init__(self, repo_path, batch_size=5, interval=10):
        self.repo_path = repo_path
        self.batch_size = batch_size
        self.interval = interval
        self.lock = asyncio.Lock()
        self.pending_images: List[Tuple[str, asyncio.Future]] = []
        self.task = None

    async def start(self):
        if self.task is None:
            self.task = asyncio.create_task(self._batch_worker())

    async def add_image(self, local_image_path):
        _, ext = os.path.splitext(local_image_path)
        unique_name = f"{uuid.uuid4().hex}{ext}"
        dest_path = os.path.join(self.repo_path, unique_name)

        subprocess.run(["cp", local_image_path, dest_path], check=True)

        url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/{unique_name}"

        future = asyncio.get_event_loop().create_future()

        async with self.lock:
            self.pending_images.append((unique_name, future))

        return url, future

    async def _batch_worker(self):
        while True:
            await asyncio.sleep(self.interval)
            await self._process_batch()

    async def _process_batch(self):
        async with self.lock:
            if not self.pending_images:
                return

            images_batch = self.pending_images[:self.batch_size]
            self.pending_images = self.pending_images[self.batch_size:]

        filenames = [name for name, _ in images_batch]

        try:
            await asyncio.get_event_loop().run_in_executor(None, self._git_push, filenames)
            for _, future in images_batch:
                future.set_result(True)
        except Exception as e:
            for _, future in images_batch:
                future.set_exception(e)

    def _git_push(self, filenames: List[str]):
        cwd = os.getcwd()
        os.chdir(self.repo_path)
        try:
            subprocess.run(["git", "pull", "--rebase"], check=True)
            subprocess.run(["git", "add"] + filenames, check=True)
            subprocess.run(["git", "commit", "-m", f"Añadir lote de {len(filenames)} imágenes"], check=True)
            subprocess.run(["git", "push", "origin", BRANCH], check=True)
        finally:
            os.chdir(cwd)
