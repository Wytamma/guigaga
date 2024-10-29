import click
import gradio as gr
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from guigaga.guigaga import GUIGAGA


@click.command()
@click.argument("text",  type=str)
def yell(text):
    """This script converts text to uppercase."""
    click.echo(text.upper())


@click.command()
@click.argument("text",  type=str)
def reverse(text):
    """This script reverses text."""
    click.echo(text[::-1])


app = FastAPI()

@app.get("/")
async def main():
    content = """
<body>
<a href="/yell/">Yell</a>
<a href="/reverse/">Reverse</a>
</body>
    """
    return HTMLResponse(content=content)

app = gr.mount_gradio_app(app, GUIGAGA(yell).interface, path="/yell")
app = gr.mount_gradio_app(app, GUIGAGA(reverse).interface, path="/reverse")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,host="localhost",port=8000)